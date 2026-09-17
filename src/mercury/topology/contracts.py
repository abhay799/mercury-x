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
    host_id: str | None = None
    rack_id: str | None = None
    zone_id: str | None = None
    region_id: str | None = None
    provider_id: str | None = None
    active: bool = True

    @field_validator("topology_node_id","hardware_profile_id")
    @classmethod
    def req(cls,v):
        return _nonblank(v, "topology node id")


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
