import hashlib, json
from enum import Enum
from pydantic import Field, field_validator, model_validator
from mercury.contracts.base import ContractModel


class TopologyLinkKind(str, Enum):
    PCIE="PCIE"; NVLINK_LIKE="NVLINK_LIKE"; HIGH_SPEED_FABRIC="HIGH_SPEED_FABRIC"
    ETHERNET="ETHERNET"; INFINIBAND="INFINIBAND"; SHARED_MEMORY="SHARED_MEMORY"; UNKNOWN="UNKNOWN"


class LocalityDomain(str, Enum):
    DEVICE="DEVICE"; HOST="HOST"; RACK="RACK"; ZONE="ZONE"; REGION="REGION"; PROVIDER="PROVIDER"; UNKNOWN="UNKNOWN"


class TopologyCapabilityState(str, Enum):
    AVAILABLE="AVAILABLE"; UNAVAILABLE="UNAVAILABLE"; UNKNOWN="UNKNOWN"


def _hash(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _nonblank(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonblank")
    return value.strip()


def _canonical_evidence_ids(values: tuple[str, ...]) -> tuple[str, ...]:
    result = tuple(_nonblank(value, "evidence_id") for value in values)
    if len(result) != len(set(result)):
        raise ValueError("evidence_ids contain duplicates")
    return tuple(sorted(result))


class TopologyNode(ContractModel):
    topology_node_id: str
    hardware_profile_id: str
    hardware_profile_generation: int | None = Field(default=None, ge=1)
    hardware_profile_fingerprint: str | None = None
    host_id: str | None = None
    rack_id: str | None = None
    zone_id: str | None = None
    region_id: str | None = None
    provider_id: str | None = None
    active: bool = True

    @field_validator("topology_node_id", "hardware_profile_id")
    @classmethod
    def req(cls,v):
        return _nonblank(v, "topology node id")

    @field_validator("hardware_profile_fingerprint")
    @classmethod
    def optional_fingerprint(cls, value):
        return None if value is None else _nonblank(value, "hardware_profile_fingerprint")

    @model_validator(mode="after")
    def complete_profile_binding(self):
        binding = (self.hardware_profile_generation, self.hardware_profile_fingerprint)
        if any(value is not None for value in binding) and any(value is None for value in binding):
            raise ValueError("hardware profile generation binding must be complete")
        return self


class TopologyLink(ContractModel):
    topology_link_id: str
    source_node_id: str
    destination_node_id: str
    link_kind: TopologyLinkKind
    bidirectional: bool
    declared_bandwidth_bytes_per_s: int | None = Field(default=None, ge=1)
    measured_bandwidth_bytes_per_s: int | None = Field(default=None, ge=1)
    declared_latency_us: float | None = Field(default=None, gt=0)
    measured_latency_us: float | None = Field(default=None, gt=0)
    evidence_ids: tuple[str,...] = ()

    @field_validator("topology_link_id", "source_node_id", "destination_node_id")
    @classmethod
    def required_ids(cls, value):
        return _nonblank(value, "topology link identity")

    @field_validator("evidence_ids")
    @classmethod
    def canonical_evidence(cls, value):
        return _canonical_evidence_ids(value)

    @model_validator(mode="after")
    def no_self(self):
        if self.source_node_id == self.destination_node_id:
            raise ValueError("self link forbidden")
        return self


class TopologyGraph(ContractModel):
    topology_graph_id: str
    nodes: tuple[TopologyNode,...]
    links: tuple[TopologyLink,...]
    generation: int = Field(ge=1)
    fingerprint: str

    @field_validator("topology_graph_id", "fingerprint")
    @classmethod
    def required_ids(cls, value):
        return _nonblank(value, "topology graph identity")

    @model_validator(mode="after")
    def validate_graph_integrity(self):
        if not self.nodes:
            raise ValueError("topology requires nodes")
        node_ids = tuple(node.topology_node_id for node in self.nodes)
        link_ids = tuple(link.topology_link_id for link in self.links)
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("duplicate topology node")
        if len(link_ids) != len(set(link_ids)):
            raise ValueError("duplicate topology link")
        node_id_set = set(node_ids)
        for link in self.links:
            if link.source_node_id not in node_id_set or link.destination_node_id not in node_id_set:
                raise ValueError("dangling topology link")
        expected_fingerprint = topology_graph_fingerprint(
            nodes=self.nodes, links=self.links, generation=self.generation
        )
        if self.fingerprint != expected_fingerprint:
            raise ValueError("topology fingerprint mismatch")
        if self.topology_graph_id != make_topology_graph_id(expected_fingerprint):
            raise ValueError("topology graph id mismatch")
        return self


PATH_RESULT_SCHEMA_VERSION = "mercury.topology-path/v1"


class PathResult(ContractModel):
    schema_version: str = PATH_RESULT_SCHEMA_VERSION
    path_result_id: str
    graph_id: str
    graph_fingerprint: str
    graph_generation: int = Field(ge=1)
    ordered_node_ids: tuple[str, ...]
    ordered_link_ids: tuple[str, ...]
    source_node_id: str
    destination_node_id: str
    locality: LocalityDomain
    declared_aggregate_latency_us: float | None = Field(default=None, gt=0)
    measured_aggregate_latency_us: float | None = Field(default=None, gt=0)
    declared_bottleneck_bandwidth_bytes_per_s: int | None = Field(default=None, ge=1)
    measured_bottleneck_bandwidth_bytes_per_s: int | None = Field(default=None, ge=1)
    metric_evidence_ids: tuple[str, ...] = ()
    capability_state: TopologyCapabilityState
    provenance_ids: tuple[str, ...] = ()
    fingerprint: str

    @field_validator(
        "path_result_id", "graph_id", "graph_fingerprint", "source_node_id",
        "destination_node_id", "fingerprint",
    )
    @classmethod
    def path_identity_text(cls, value, info):
        return _nonblank(value, info.field_name)

    @field_validator("ordered_node_ids", "ordered_link_ids", "metric_evidence_ids", "provenance_ids")
    @classmethod
    def path_collections(cls, value, info):
        values = tuple(_nonblank(item, info.field_name) for item in value)
        if info.field_name in {"metric_evidence_ids", "provenance_ids"}:
            if len(values) != len(set(values)):
                raise ValueError(f"{info.field_name} contains duplicates")
            return tuple(sorted(values))
        return values

    @model_validator(mode="after")
    def validate_path_identity(self):
        if self.schema_version != PATH_RESULT_SCHEMA_VERSION:
            raise ValueError("unsupported path result schema")
        if self.capability_state is TopologyCapabilityState.AVAILABLE:
            if not self.ordered_node_ids or self.ordered_node_ids[0] != self.source_node_id or self.ordered_node_ids[-1] != self.destination_node_id:
                raise ValueError("available path endpoints do not match ordered nodes")
            if len(self.ordered_link_ids) != max(0, len(self.ordered_node_ids) - 1):
                raise ValueError("available path node/link shape mismatch")
        elif self.ordered_node_ids or self.ordered_link_ids:
            raise ValueError("unavailable or unknown path cannot contain route")
        expected_fingerprint = path_result_fingerprint(self)
        if self.fingerprint != expected_fingerprint:
            raise ValueError("path result fingerprint mismatch")
        if self.path_result_id != _hash({"path_result": expected_fingerprint}):
            raise ValueError("path result identity mismatch")
        return self


def make_topology_node_id(hardware_profile_id: str) -> str:
    return _hash({"hardware_profile_id": hardware_profile_id})


def make_topology_link_id(source_node_id: str, destination_node_id: str, link_kind: TopologyLinkKind, bidirectional: bool) -> str:
    return _hash({"s":source_node_id,"d":destination_node_id,"k":link_kind.value,"b":bidirectional})


def topology_graph_fingerprint(*, nodes: tuple[TopologyNode, ...], links: tuple[TopologyLink, ...], generation: int) -> str:
    return _hash({
        "nodes": [node.model_dump(mode="json") for node in nodes],
        "links": [link.model_dump(mode="json") for link in links],
        "generation": generation,
    })


def make_topology_graph_id(fingerprint: str) -> str:
    if not isinstance(fingerprint, str) or not fingerprint.strip():
        raise ValueError("topology fingerprint must be nonblank")
    return _hash({"topology_fingerprint": fingerprint})


def path_result_fingerprint(path_result: PathResult) -> str:
    payload = path_result.model_dump(mode="json", exclude={"path_result_id", "fingerprint"})
    return _hash(payload)


def make_path_result_id(fingerprint: str) -> str:
    return _hash({"path_result": _nonblank(fingerprint, "path_result fingerprint")})
