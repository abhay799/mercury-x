from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from .base import ContractModel


_PHYSICAL_EXECUTION_ASSIGNMENT_FIELDS = frozenset(
    {
        "model_assignments",
        "precision_assignments",
        "hardware_assignments",
        "context_placements",
    }
)


class _FrozenDict(dict[str, Any]):
    """JSON-serializable mapping that rejects post-validation mutation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        dict.__init__(self, *args, **kwargs)

    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("execution graph metadata is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable


def _freeze_metadata_value(value: Any) -> Any:
    if isinstance(value, (set, frozenset)):
        raise ValueError("logical graph metadata cannot contain set-like values")
    if isinstance(value, dict):
        physical_assignments = set(value) & _PHYSICAL_EXECUTION_ASSIGNMENT_FIELDS
        if physical_assignments:
            assignment_names = ", ".join(sorted(physical_assignments))
            raise ValueError(
                "logical graph metadata cannot contain physical execution assignment: "
                f"{assignment_names}"
            )
        return _FrozenDict({key: _freeze_metadata_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_metadata_value(item) for item in value)
    return value


def _freeze_metadata(metadata: dict[str, Any]) -> _FrozenDict:
    frozen_metadata = _freeze_metadata_value(metadata)
    assert isinstance(frozen_metadata, _FrozenDict)
    return frozen_metadata


class GraphNode(ContractModel):
    """A logical operation in a versioned execution-graph boundary contract."""

    node_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    node_type: str = Field(min_length=1)
    capability_required: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_metadata(self):
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))
        return self


class GraphEdge(ContractModel):
    """A logical dependency between two graph nodes."""

    edge_id: str = Field(min_length=1)
    source_node: str = Field(min_length=1)
    target_node: str = Field(min_length=1)
    edge_type: str = Field(min_length=1)
    condition: str | None = None


class ExecutionGraph(ContractModel):
    """Strict, physical-placement-independent logical DAG contract."""

    schema_version: Literal["mercury.execution.graph/v1"] = "mercury.execution.graph/v1"
    graph_id: str = Field(min_length=1)
    workload_id: str = Field(min_length=1)
    graph_version: str = Field(default="1", min_length=1)
    nodes: tuple[GraphNode, ...] = Field(default_factory=tuple)
    edges: tuple[GraphEdge, ...] = Field(default_factory=tuple)
    entry_nodes: tuple[str, ...] = Field(default_factory=tuple)
    terminal_nodes: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_logical_dag(self):
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("duplicate graph node_id")

        edge_ids = [edge.edge_id for edge in self.edges]
        if len(edge_ids) != len(set(edge_ids)):
            raise ValueError("duplicate graph edge_id")

        known_nodes = set(node_ids)
        for edge in self.edges:
            if edge.source_node not in known_nodes:
                raise ValueError(f"edge source_node not found: {edge.source_node}")
            if edge.target_node not in known_nodes:
                raise ValueError(f"edge target_node not found: {edge.target_node}")

        for node_id in self.entry_nodes:
            if node_id not in known_nodes:
                raise ValueError(f"entry_node not found: {node_id}")
        for node_id in self.terminal_nodes:
            if node_id not in known_nodes:
                raise ValueError(f"terminal_node not found: {node_id}")

        adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        for edge in self.edges:
            adjacency[edge.source_node].append(edge.target_node)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> bool:
            if node_id in visiting:
                return True
            if node_id in visited:
                return False
            visiting.add(node_id)
            for target_id in adjacency[node_id]:
                if visit(target_id):
                    return True
            visiting.remove(node_id)
            visited.add(node_id)
            return False

        if any(visit(node_id) for node_id in node_ids):
            raise ValueError("execution graph must be acyclic")

        return self
