from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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