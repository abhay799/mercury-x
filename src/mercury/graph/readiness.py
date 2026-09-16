"""Read-only readiness gating for validated logical execution graphs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mercury.graph.models import ExecutionGraph, Evidence
from mercury.graph.transformation import ExecutionGraphTransformationResult
from mercury.graph.validation import ExecutionGraphValidationResult, GraphValidationStatus


class GraphReadinessStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class GraphReadinessIssue:
    invariant: str
    reason: str
    affected_artifact: str | None = None

    def __post_init__(self) -> None:
        if not self.invariant.strip():
            raise ValueError("invariant must be nonblank")
        if not self.reason.strip():
            raise ValueError("reason must be nonblank")


@dataclass(frozen=True)
class GraphReadinessEvidence:
    invariant: str
    passed: bool
    reason: str

    def __post_init__(self) -> None:
        if not self.invariant.strip() or not self.reason.strip():
            raise ValueError("readiness evidence must be nonblank")


@dataclass(frozen=True)
class GraphReadinessResult:
    graph_id: str
    request_id: str
    workload_id: str
    session_id: str
    status: GraphReadinessStatus
    issues: tuple[GraphReadinessIssue, ...]
    evidence: tuple[GraphReadinessEvidence, ...]

    def __post_init__(self) -> None:
        issues = tuple(sorted(set(self.issues), key=lambda item: (item.invariant, item.affected_artifact or "", item.reason)))
        evidence = tuple(sorted(set(self.evidence), key=lambda item: item.invariant))
        if not evidence:
            raise ValueError("readiness evidence must not be empty")
        if self.status is GraphReadinessStatus.READY and issues:
            raise ValueError("READY graph cannot have blocking issues")
        object.__setattr__(self, "issues", issues)
        object.__setattr__(self, "evidence", evidence)


_FORBIDDEN_FIELDS = frozenset(
    {
        "model_id", "provider", "model_family", "concrete_model", "cpu", "gpu",
        "accelerator", "hardware", "device", "host", "region", "placement",
        "scheduler_assignment", "runtime_process", "container", "pod", "precision",
        "migration", "speculative_execution", "cost_optimization",
    }
)


def evaluate_graph_readiness(
    graph: ExecutionGraph,
    validation: ExecutionGraphValidationResult,
    transformation: ExecutionGraphTransformationResult | None = None,
) -> GraphReadinessResult:
    """Determine whether validated logical artifacts are ready to leave Phase 3."""
    if not isinstance(graph, ExecutionGraph) or not isinstance(validation, ExecutionGraphValidationResult):
        raise ValueError("readiness requires graph and validation contracts")
    issues: list[GraphReadinessIssue] = []
    evidence: list[GraphReadinessEvidence] = []

    def check(invariant: str, passed: bool, reason: str, artifact: str | None = None) -> None:
        evidence.append(GraphReadinessEvidence(invariant, passed, reason))
        if not passed:
            issues.append(GraphReadinessIssue(invariant, reason, artifact))

    identity = (graph.request_id, graph.workload_id, graph.session_id)
    identity_valid = all(isinstance(value, str) and value.strip() for value in identity) and isinstance(graph.graph_id, str) and bool(graph.graph_id.strip())
    check("identity", identity_valid and validation.graph_id == graph.graph_id, "graph and validation identities must be nonblank and consistent", "validation")
    check("semantic_validation", validation.status is GraphValidationStatus.PASS, "Task 3 semantic validation must PASS", "validation")

    graph_provenance_valid = bool(graph.provenance) and all(isinstance(item, Evidence) and item.source.strip() and item.reason.strip() for item in graph.provenance)
    nodes_provenance_valid = all(node.evidence and all(isinstance(item, Evidence) and item.source.strip() and item.reason.strip() for item in node.evidence) for node in graph.nodes)
    check("provenance", graph_provenance_valid and nodes_provenance_valid, "graph and logical nodes require nonblank provenance", "graph")

    transformation_valid = True
    transformation_reason = "no topology-changing transformation was supplied"
    if transformation is not None:
        transformation_valid = isinstance(transformation, ExecutionGraphTransformationResult)
        if transformation_valid:
            transformation_valid = transformation.graph == graph and bool(transformation.records)
            if transformation.changed:
                transformation_valid = transformation_valid and all(record.reason.strip() for record in transformation.records)
            transformation_reason = "transformation artifact must preserve graph identity and nonblank records"
        else:
            transformation_reason = "transformation artifact is unsupported"
    check("transformation", transformation_valid, transformation_reason, "transformation")

    leaked = tuple(sorted(_FORBIDDEN_FIELDS.intersection(vars(graph))))
    check("phase_boundary", not leaked, "logical graph must not expose physical execution decision fields", "graph")

    status = GraphReadinessStatus.BLOCKED if issues else GraphReadinessStatus.READY
    return GraphReadinessResult(
        graph_id=graph.graph_id,
        request_id=graph.request_id,
        workload_id=graph.workload_id,
        session_id=graph.session_id,
        status=status,
        issues=tuple(issues),
        evidence=tuple(evidence),
    )
