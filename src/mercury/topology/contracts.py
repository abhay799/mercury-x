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
        if not v or not v.strip(): raise ValueError("nonblank id required")
        return v


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


def make_topology_node_id(hardware_profile_id: str) -> str:
    return _hash({"hardware_profile_id": hardware_profile_id})


def make_topology_link_id(source_node_id: str, destination_node_id: str, link_kind: TopologyLinkKind, bidirectional: bool) -> str:
    return _hash({"s":source_node_id,"d":destination_node_id,"k":link_kind.value,"b":bidirectional})
