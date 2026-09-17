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
        for branch_id in self.losing_branch_ids:
            _nonblank(branch_id, "losing_branch_id")
            if branch_id == self.winning_branch_id:
                raise ValueError("winner cannot be a losing branch")
        if self.result_fingerprint != sh(speculative_result_payload(self)):
            raise ValueError("speculative result fingerprint mismatch")
        return self
