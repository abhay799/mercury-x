from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from mercury.intelligence.models import ComputationalCapability, Evidence, WorkloadIntelligenceProfile


class NodeType(str, Enum):
    INPUT = "input"
    PARSER = "parser"
    ENCODER = "encoder"
    EMBEDDING = "embedding"
    RETRIEVAL = "retrieval"
    RERANK = "rerank"
    VISION = "vision"
    REASONING = "reasoning"
    CODE_EXECUTION = "code_execution"
    TOOL_EXECUTION = "tool_execution"
    GENERATION = "generation"
    CRITIC = "critic"
    VERIFICATION = "verification"
    SYNTHESIS = "synthesis"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    ROUTER = "router"
    MERGE = "merge"
    OUTPUT = "output"


class EdgeType(str, Enum):
    DATA = "data"
    CONTROL = "control"
    CONTEXT = "context"
    CONDITIONAL = "conditional"
    SPECULATIVE = "speculative"
    FALLBACK = "fallback"
    VERIFICATION = "verification"


class NodeState(str, Enum):
    CREATED = "created"
    READY = "ready"
    QUEUED = "queued"
    PLACED = "placed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CHECKPOINTING = "checkpointing"
    SUSPENDED = "suspended"
    MIGRATING = "migrating"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class ExecutionNode(BaseModel):
    node_id: UUID = Field(default_factory=uuid4)

    name: str = Field(min_length=1)
    node_type: NodeType

    capability_required: str = Field(min_length=1)

    state: NodeState = NodeState.CREATED

    max_latency_ms: Optional[int] = Field(default=None, gt=0)
    max_cost: Optional[float] = Field(default=None, ge=0)

    retry_limit: int = Field(default=0, ge=0)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionEdge(BaseModel):
    edge_id: UUID = Field(default_factory=uuid4)

    source_node: UUID
    target_node: UUID

    edge_type: EdgeType = EdgeType.DATA

    condition: Optional[str] = None


class AIExecutionGraph(BaseModel):
    graph_id: UUID = Field(default_factory=uuid4)

    workload_id: UUID
    graph_version: str = "0.1"

    nodes: List[ExecutionNode] = Field(default_factory=list)
    edges: List[ExecutionEdge] = Field(default_factory=list)

    entry_nodes: List[UUID] = Field(default_factory=list)
    terminal_nodes: List[UUID] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphNodeType(str, Enum):
    INPUT = "input"
    PREPROCESS = "preprocess"
    REASONING = "reasoning"
    RETRIEVAL = "retrieval"
    TOOL = "tool"
    TRANSFORM = "transform"
    AGGREGATE = "aggregate"
    OUTPUT = "output"
    VALIDATION = "validation"


class GraphDependencyType(str, Enum):
    DATA = "data"
    CONTROL = "control"
    CONTEXT = "context"
    TOOL_RESULT = "tool_result"


class ExecutionGraphStatus(str, Enum):
    DECLARED = "declared"


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _evidence(values: Iterable[Evidence], field_name: str) -> tuple[Evidence, ...]:
    normalized = tuple(sorted(set(values), key=lambda item: (item.source, item.reason)))
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if any(not isinstance(item, Evidence) for item in normalized):
        raise ValueError(f"{field_name} must contain Evidence values")
    return normalized


@dataclass(frozen=True)
class ExecutionGraphNode:
    """A logical operation in a DAG, independent of concrete execution resources."""

    node_id: str
    node_type: GraphNodeType
    purpose: str
    required_capabilities: tuple[ComputationalCapability, ...]
    evidence: tuple[Evidence, ...]
    input_references: tuple[str, ...] = ()
    output_contract: str | None = None

    def __post_init__(self) -> None:
        _nonblank(self.node_id, "node_id")
        _nonblank(self.purpose, "purpose")
        if not isinstance(self.node_type, GraphNodeType):
            raise ValueError("node_type must be a GraphNodeType")
        capabilities = tuple(sorted(set(self.required_capabilities), key=lambda item: item.value))
        if not capabilities:
            raise ValueError("required_capabilities must not be empty")
        if any(not isinstance(item, ComputationalCapability) for item in capabilities):
            raise ValueError("required_capabilities must contain ComputationalCapability values")
        references = tuple(sorted(set(self.input_references)))
        if any(not isinstance(item, str) or not item.strip() for item in references):
            raise ValueError("input_references must be nonblank")
        if self.output_contract is not None:
            _nonblank(self.output_contract, "output_contract")
        object.__setattr__(self, "required_capabilities", capabilities)
        object.__setattr__(self, "input_references", references)
        object.__setattr__(self, "evidence", _evidence(self.evidence, "evidence"))


@dataclass(frozen=True)
class ExecutionGraphEdge:
    source_node_id: str
    target_node_id: str
    dependency_type: GraphDependencyType
    evidence: tuple[Evidence, ...]

    def __post_init__(self) -> None:
        _nonblank(self.source_node_id, "source_node_id")
        _nonblank(self.target_node_id, "target_node_id")
        if not isinstance(self.dependency_type, GraphDependencyType):
            raise ValueError("dependency_type must be a GraphDependencyType")
        object.__setattr__(self, "evidence", _evidence(self.evidence, "evidence"))


@dataclass(frozen=True)
class ExecutionGraph:
    graph_id: str
    request_id: str
    workload_id: str
    session_id: str
    nodes: tuple[ExecutionGraphNode, ...]
    edges: tuple[ExecutionGraphEdge, ...]
    provenance: tuple[Evidence, ...]
    intelligence_profile: WorkloadIntelligenceProfile | None = None
    status: ExecutionGraphStatus = ExecutionGraphStatus.DECLARED
    version: str = "mercury.execution-graph/v1"

    def __post_init__(self) -> None:
        for name in ("graph_id", "request_id", "workload_id", "session_id", "version"):
            _nonblank(getattr(self, name), name)
        if not isinstance(self.status, ExecutionGraphStatus):
            raise ValueError("status must be an ExecutionGraphStatus")
        nodes = tuple(sorted(self.nodes, key=lambda item: item.node_id))
        if not nodes:
            raise ValueError("nodes must not be empty")
        if any(not isinstance(item, ExecutionGraphNode) for item in nodes):
            raise ValueError("nodes must contain ExecutionGraphNode values")
        node_ids = tuple(item.node_id for item in nodes)
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("node ids must be unique")
        edges = tuple(sorted(set(self.edges), key=lambda item: (item.source_node_id, item.target_node_id, item.dependency_type.value)))
        if any(not isinstance(item, ExecutionGraphEdge) for item in edges):
            raise ValueError("edges must contain ExecutionGraphEdge values")
        node_id_set = set(node_ids)
        for edge in edges:
            if edge.source_node_id not in node_id_set:
                raise ValueError("edge source node must exist")
            if edge.target_node_id not in node_id_set:
                raise ValueError("edge target node must exist")
            if edge.source_node_id == edge.target_node_id:
                raise ValueError("self-edge is not allowed")
        if self.intelligence_profile is not None:
            if not isinstance(self.intelligence_profile, WorkloadIntelligenceProfile):
                raise ValueError("intelligence_profile must be a WorkloadIntelligenceProfile")
            if (self.intelligence_profile.request_id, self.intelligence_profile.workload_id, self.intelligence_profile.session_id) != (self.request_id, self.workload_id, self.session_id):
                raise ValueError("intelligence profile identity does not match graph identity")
        if self._contains_cycle(node_id_set, edges):
            raise ValueError("graph cycle is not allowed in the DAG baseline")
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "edges", edges)
        object.__setattr__(self, "provenance", _evidence(self.provenance, "provenance"))

    @staticmethod
    def _contains_cycle(node_ids: set[str], edges: tuple[ExecutionGraphEdge, ...]) -> bool:
        incoming = {node_id: 0 for node_id in node_ids}
        outgoing = {node_id: [] for node_id in node_ids}
        for edge in edges:
            incoming[edge.target_node_id] += 1
            outgoing[edge.source_node_id].append(edge.target_node_id)
        ready = sorted(node_id for node_id, count in incoming.items() if count == 0)
        visited = 0
        while ready:
            current = ready.pop(0)
            visited += 1
            for target in sorted(outgoing[current]):
                incoming[target] -= 1
                if incoming[target] == 0:
                    ready.append(target)
        return visited != len(node_ids)
