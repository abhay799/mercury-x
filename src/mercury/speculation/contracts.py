import hashlib
import json
from enum import Enum

from pydantic import Field, model_validator

from mercury.contracts.base import ContractModel
from mercury.global_memory.contracts import GlobalMemoryNamespace


MAX_SPECULATIVE_BRANCHES = 8


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def sh(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


class SpeculativeBranchState(str, Enum):
    PLANNED = "PLANNED"
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    COMMITTED = "COMMITTED"
    DISCARDED = "DISCARDED"


class SpeculativeBranchEventType(str, Enum):
    PLANNED = "PLANNED"
    READY = "READY"
    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    COMMITTED = "COMMITTED"
    CANCELLED = "CANCELLED"
    DISCARDED = "DISCARDED"


class SpeculationRetryMetadata(ContractModel):
    retry_supported: bool = False
    retry_attempt: int = Field(default=0, ge=0)
    maximum_attempts: int = Field(default=0, ge=0)
    parent_branch_id: str | None = None
    reason: str | None = None
    generation: int = Field(default=1, ge=1)
    provenance_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def retries_are_not_supported(self):
        if self.retry_supported or self.retry_attempt or self.maximum_attempts or self.parent_branch_id or self.reason or self.provenance_ids:
            raise ValueError("retry is not supported by the Phase 16 baseline")
        return self


class SpeculationAccounting(ContractModel):
    total_planned_branches: int = Field(ge=1, le=MAX_SPECULATIVE_BRANCHES)
    started_branches: int = Field(ge=0, le=MAX_SPECULATIVE_BRANCHES)
    succeeded_branches: int = Field(ge=0, le=MAX_SPECULATIVE_BRANCHES)
    failed_branches: int = Field(ge=0, le=MAX_SPECULATIVE_BRANCHES)
    verified_success_branches: int = Field(ge=0, le=MAX_SPECULATIVE_BRANCHES)
    cancelled_branches: int = Field(ge=0, le=MAX_SPECULATIVE_BRANCHES)
    discarded_branches: int = Field(ge=0, le=MAX_SPECULATIVE_BRANCHES)
    authoritative_committed_branch_id: str
    verification_count: int = Field(ge=0, le=MAX_SPECULATIVE_BRANCHES)
    verification_overhead_units: float | None = Field(default=None, ge=0)
    speculative_resource_estimate_units: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def accounting_bounds(self):
        _nonblank(self.authoritative_committed_branch_id, "authoritative_committed_branch_id")
        values = (self.started_branches, self.succeeded_branches, self.failed_branches,
                  self.verified_success_branches, self.cancelled_branches,
                  self.discarded_branches, self.verification_count)
        if any(value > self.total_planned_branches for value in values):
            raise ValueError("branch accounting exceeds planned branches")
        if self.verified_success_branches > self.succeeded_branches:
            raise ValueError("verified success accounting exceeds succeeded branches")
        return self


class SpeculationUpstreamProvenance(ContractModel):
    candidate_id: str
    candidate_fingerprint: str
    hardware_profile_id: str
    hardware_profile_generation: int = Field(ge=1)
    hardware_profile_fingerprint: str
    topology_graph_id: str
    topology_generation: int = Field(ge=1)
    path_result_id: str
    path_result_fingerprint: str
    prediction_id: str | None = None
    prediction_fingerprint: str | None = None

    @model_validator(mode="after")
    def complete_upstream_lineage(self):
        for name in (
            "candidate_id", "candidate_fingerprint", "hardware_profile_id",
            "hardware_profile_fingerprint", "topology_graph_id", "path_result_id",
            "path_result_fingerprint",
        ):
            _nonblank(getattr(self, name), name)
        if (self.prediction_id is None) != (self.prediction_fingerprint is None):
            raise ValueError("prediction provenance must be complete")
        if self.prediction_id is not None:
            _nonblank(self.prediction_id, "prediction_id")
            _nonblank(self.prediction_fingerprint, "prediction_fingerprint")
        return self


def speculation_plan_payload(plan: "SpeculationPlan") -> dict:
    return {
        "source_segment_id": plan.source_segment_id,
        "placement_candidate_ids": plan.placement_candidate_ids,
        "candidate_fingerprints": plan.candidate_fingerprints,
        "max_branches": plan.max_branches,
        "verification_policy_id": plan.verification_policy_id,
        "commit_policy_id": plan.commit_policy_id,
        "cancellation_policy_id": plan.cancellation_policy_id,
        "source_execution_plan_id": plan.source_execution_plan_id,
        "namespace_type": plan.namespace_type.value if plan.namespace_type else None,
        "namespace_id": plan.namespace_id,
        "source_segment_fingerprint": plan.source_segment_fingerprint,
        "upstream_provenance": [item.model_dump(mode="json") for item in plan.upstream_provenance],
    }


class SpeculationPlan(ContractModel):
    speculation_plan_id: str
    source_segment_id: str
    placement_candidate_ids: tuple[str, ...]
    candidate_fingerprints: tuple[tuple[str, str], ...]
    max_branches: int = Field(ge=1, le=MAX_SPECULATIVE_BRANCHES)
    verification_policy_id: str
    commit_policy_id: str
    cancellation_policy_id: str
    fingerprint: str
    source_execution_plan_id: str | None = None
    namespace_type: GlobalMemoryNamespace | None = None
    namespace_id: str | None = None
    source_segment_fingerprint: str | None = None
    upstream_provenance: tuple[SpeculationUpstreamProvenance, ...] = ()

    @model_validator(mode="after")
    def bounded(self):
        for field_name in (
            "speculation_plan_id",
            "source_segment_id",
            "verification_policy_id",
            "commit_policy_id",
            "cancellation_policy_id",
            "fingerprint",
        ):
            _nonblank(getattr(self, field_name), field_name)
        if not self.placement_candidate_ids:
            raise ValueError("placement_candidate_ids must be nonempty")
        for candidate_id in self.placement_candidate_ids:
            _nonblank(candidate_id, "placement_candidate_id")
        if len(self.placement_candidate_ids) > self.max_branches:
            raise ValueError("branch count exceeds plan bound")
        if self.placement_candidate_ids != tuple(sorted(self.placement_candidate_ids)):
            raise ValueError("placement_candidate_ids must be canonical")
        if len(self.placement_candidate_ids) != len(set(self.placement_candidate_ids)):
            raise ValueError("duplicate candidate")
        if tuple(pair[0] for pair in self.candidate_fingerprints) != self.placement_candidate_ids:
            raise ValueError("candidate fingerprints must match plan candidates")
        if len(self.candidate_fingerprints) != len(set(self.candidate_fingerprints)):
            raise ValueError("duplicate candidate fingerprint")
        for candidate_id, fingerprint in self.candidate_fingerprints:
            _nonblank(candidate_id, "candidate fingerprint id")
            _nonblank(fingerprint, "candidate fingerprint")

        typed_context = (
            self.source_execution_plan_id,
            self.namespace_type,
            self.namespace_id,
            self.source_segment_fingerprint,
        )
        if any(value is not None for value in typed_context):
            if any(value is None for value in typed_context):
                raise ValueError("typed source context must be complete")
            _nonblank(self.source_execution_plan_id, "source_execution_plan_id")
            _nonblank(self.namespace_id, "namespace_id")
            _nonblank(self.source_segment_fingerprint, "source_segment_fingerprint")
        provenance_ids = tuple(item.candidate_id for item in self.upstream_provenance)
        if provenance_ids and provenance_ids != self.placement_candidate_ids:
            raise ValueError("upstream provenance must match placement candidates")
        if self.fingerprint != sh(speculation_plan_payload(self)):
            raise ValueError("speculation plan fingerprint mismatch")
        if self.speculation_plan_id != sh({"plan": self.fingerprint}):
            raise ValueError("speculation plan identity mismatch")
        return self


class SpeculativeBranch(ContractModel):
    branch_id: str
    placement_candidate_id: str
    state: SpeculativeBranchState
    speculation_plan_id: str | None = None
    source_segment_id: str | None = None
    plan_fingerprint: str | None = None
    candidate_fingerprint: str | None = None
    result_id: str | None = None
    result_fingerprint: str | None = None
    verification_evidence_id: str | None = None
    verified: bool = False
    generation: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def valid_state(self):
        for field_name in ("branch_id", "placement_candidate_id"):
            _nonblank(getattr(self, field_name), field_name)
        branch_context = (
            self.speculation_plan_id,
            self.source_segment_id,
            self.plan_fingerprint,
            self.candidate_fingerprint,
        )
        if any(value is not None for value in branch_context):
            if any(value is None for value in branch_context):
                raise ValueError("branch provenance context must be complete")
            for field_name in (
                "speculation_plan_id",
                "source_segment_id",
                "plan_fingerprint",
                "candidate_fingerprint",
            ):
                _nonblank(getattr(self, field_name), field_name)
        if self.result_id is not None:
            _nonblank(self.result_id, "result_id")
        if self.result_fingerprint is not None:
            _nonblank(self.result_fingerprint, "result_fingerprint")
        if self.verification_evidence_id is not None:
            _nonblank(self.verification_evidence_id, "verification_evidence_id")
        if self.state in {SpeculativeBranchState.SUCCEEDED, SpeculativeBranchState.COMMITTED}:
            if self.result_id is None or self.result_fingerprint is None:
                raise ValueError("successful branch requires result provenance")
        if self.verified and self.verification_evidence_id is None:
            raise ValueError("verified branch requires verification evidence")
        if self.state is SpeculativeBranchState.COMMITTED and (not self.verified or self.result_id is None):
            raise ValueError("committed branch requires verified result")
        return self


def speculative_result_payload(result: "SpeculativeResult") -> dict:
    return {
        "speculation_plan_id": result.speculation_plan_id,
        "source_segment_id": result.source_segment_id,
        "source_execution_plan_id": result.source_execution_plan_id,
        "namespace_type": result.namespace_type.value if result.namespace_type else None,
        "namespace_id": result.namespace_id,
        "plan_fingerprint": result.plan_fingerprint,
        "winning_branch_id": result.winning_branch_id,
        "committed_result_id": result.committed_result_id,
        "winning_result_fingerprint": result.winning_result_fingerprint,
        "verification_evidence_id": result.verification_evidence_id,
        "losing_branch_ids": result.losing_branch_ids,
        "branch_count": result.branch_count,
        "verified_success_count": result.verified_success_count,
        "accounting": result.accounting.model_dump(mode="json"),
    }


class SpeculativeResult(ContractModel):
    speculation_plan_id: str
    source_segment_id: str
    source_execution_plan_id: str | None = None
    namespace_type: GlobalMemoryNamespace | None = None
    namespace_id: str | None = None
    plan_fingerprint: str
    winning_branch_id: str
    committed_result_id: str
    winning_result_fingerprint: str
    verification_evidence_id: str
    losing_branch_ids: tuple[str, ...]
    branch_count: int = Field(ge=1, le=MAX_SPECULATIVE_BRANCHES)
    verified_success_count: int = Field(ge=1, le=MAX_SPECULATIVE_BRANCHES)
    accounting: SpeculationAccounting
    result_fingerprint: str

    @model_validator(mode="after")
    def valid_result(self):
        for field_name in (
            "speculation_plan_id",
            "source_segment_id",
            "plan_fingerprint",
            "winning_branch_id",
            "committed_result_id",
            "winning_result_fingerprint",
            "verification_evidence_id",
            "result_fingerprint",
        ):
            _nonblank(getattr(self, field_name), field_name)
        typed_context = (self.source_execution_plan_id, self.namespace_type, self.namespace_id)
        if any(value is not None for value in typed_context):
            if any(value is None for value in typed_context):
                raise ValueError("result typed source context must be complete")
            _nonblank(self.source_execution_plan_id, "source_execution_plan_id")
            _nonblank(self.namespace_id, "namespace_id")
        if len(self.losing_branch_ids) != len(set(self.losing_branch_ids)):
            raise ValueError("duplicate losing branch")
        if self.branch_count != len(self.losing_branch_ids) + 1:
            raise ValueError("branch accounting does not match result lineage")
        if self.verified_success_count > self.branch_count:
            raise ValueError("verified success accounting exceeds branch count")
        if (
            self.accounting.total_planned_branches != self.branch_count
            or self.accounting.verified_success_branches != self.verified_success_count
            or self.accounting.authoritative_committed_branch_id != self.winning_branch_id
        ):
            raise ValueError("detailed accounting does not match result")
        for branch_id in self.losing_branch_ids:
            _nonblank(branch_id, "losing_branch_id")
            if branch_id == self.winning_branch_id:
                raise ValueError("winner cannot be a losing branch")
        if self.result_fingerprint != sh(speculative_result_payload(self)):
            raise ValueError("speculative result fingerprint mismatch")
        return self


class SpeculativeBranchEvent(ContractModel):
    event_id: str
    speculation_plan_id: str
    branch_id: str
    candidate_id: str
    event_type: SpeculativeBranchEventType
    from_state: SpeculativeBranchState
    to_state: SpeculativeBranchState
    generation: int = Field(ge=1)
    event_sequence: int = Field(ge=1)
    provenance_ids: tuple[str, ...]
    fingerprint: str

    @model_validator(mode="after")
    def event_integrity(self):
        for name in ("event_id", "speculation_plan_id", "branch_id", "candidate_id", "fingerprint"):
            _nonblank(getattr(self, name), name)
        if not self.provenance_ids or any(not item.strip() for item in self.provenance_ids):
            raise ValueError("branch event requires nonblank provenance")
        if tuple(sorted(self.provenance_ids)) != self.provenance_ids or len(set(self.provenance_ids)) != len(self.provenance_ids):
            raise ValueError("branch event provenance must be canonical")
        expected = sh(branch_event_payload(self))
        if self.fingerprint != expected or self.event_id != sh({"branch_event": expected}):
            raise ValueError("branch event identity mismatch")
        legal = {
            SpeculativeBranchEventType.READY: (SpeculativeBranchState.PLANNED, SpeculativeBranchState.READY),
            SpeculativeBranchEventType.STARTED: (SpeculativeBranchState.READY, SpeculativeBranchState.RUNNING),
            SpeculativeBranchEventType.SUCCEEDED: (SpeculativeBranchState.RUNNING, SpeculativeBranchState.SUCCEEDED),
            SpeculativeBranchEventType.FAILED: (SpeculativeBranchState.RUNNING, SpeculativeBranchState.FAILED),
            SpeculativeBranchEventType.VERIFICATION_PASSED: (SpeculativeBranchState.SUCCEEDED, SpeculativeBranchState.SUCCEEDED),
            SpeculativeBranchEventType.VERIFICATION_FAILED: (SpeculativeBranchState.SUCCEEDED, SpeculativeBranchState.FAILED),
            SpeculativeBranchEventType.COMMITTED: (SpeculativeBranchState.SUCCEEDED, SpeculativeBranchState.COMMITTED),
            SpeculativeBranchEventType.CANCELLED: (self.from_state, SpeculativeBranchState.CANCELLED),
            SpeculativeBranchEventType.DISCARDED: (self.from_state, SpeculativeBranchState.DISCARDED),
        }
        expected_transition = legal.get(self.event_type)
        if expected_transition is None or expected_transition != (self.from_state, self.to_state):
            raise ValueError("illegal branch event state combination")
        return self


def branch_event_payload(event: SpeculativeBranchEvent) -> dict:
    return event.model_dump(mode="json", exclude={"event_id", "fingerprint"})
