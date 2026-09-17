import hashlib
import json
from enum import Enum

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.global_memory.contracts import GlobalMemoryNamespace


MAX_SEGMENTS_PER_EXECUTION_PLAN = 256
MAX_DEPENDENCIES_PER_SEGMENT = 64
MAX_HANDOFFS_PER_SEGMENT = 64
MAX_EXECUTION_ARTIFACTS_PER_SEGMENT = 128
MAX_RETRY_ATTEMPTS = 8


class ExecutionSegmentType(str, Enum):
    PREFILL = "PREFILL"
    DECODE = "DECODE"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    RETRIEVAL = "RETRIEVAL"
    TRANSFORM = "TRANSFORM"
    AGGREGATION = "AGGREGATION"


class ExecutionSegmentState(str, Enum):
    PLANNED = "PLANNED"
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExecutionHandoffKind(str, Enum):
    ARTIFACT = "ARTIFACT"
    CONTEXT = "CONTEXT"
    KV_REFERENCE = "KV_REFERENCE"
    CONTROL = "CONTROL"


class ExecutionHandoffState(str, Enum):
    PENDING = "PENDING"
    AVAILABLE = "AVAILABLE"
    CONSUMED = "CONSUMED"
    INVALIDATED = "INVALIDATED"


class ExecutionFailureCategory(str, Enum):
    INPUT_FAILURE = "INPUT_FAILURE"
    HANDOFF_FAILURE = "HANDOFF_FAILURE"
    COMPATIBILITY_FAILURE = "COMPATIBILITY_FAILURE"
    RUNTIME_FAILURE = "RUNTIME_FAILURE"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    CANCELLED_FAILURE = "CANCELLED_FAILURE"


def _nonblank(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonblank")
    return value


def _canonical_tuple(values, field: str, max_items: int | None = None) -> tuple[str, ...]:
    result = tuple(values)
    for item in result:
        _nonblank(item, field)
    if len(result) != len(set(result)):
        raise ValueError(f"{field} contains duplicates")
    if result != tuple(sorted(result)):
        raise ValueError(f"{field} must be canonical")
    if max_items is not None and len(result) > max_items:
        raise ValueError(f"{field} exceeds certified limit")
    return result


def _stable_hash(payload: dict) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class ExecutionRetryPolicy(ContractModel):
    retry_policy_id: str
    max_attempts: int = Field(ge=1, le=MAX_RETRY_ATTEMPTS)
    retryable_failure_categories: tuple[ExecutionFailureCategory, ...] = ()

    @field_validator("retry_policy_id")
    @classmethod
    def validate_id(cls, value):
        return _nonblank(value, "retry_policy_id")

    @field_validator("retryable_failure_categories")
    @classmethod
    def validate_categories(cls, value):
        values = tuple(value)
        if len(values) != len(set(values)):
            raise ValueError("duplicate retry category")
        if tuple(sorted(x.value for x in values)) != tuple(x.value for x in values):
            raise ValueError("retry categories must be canonical")
        return values


class ExecutionSegment(ContractModel):
    segment_id: str
    execution_plan_id: str
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    segment_type: ExecutionSegmentType
    input_artifact_ids: tuple[str, ...] = ()
    output_contract_id: str
    model_requirement_id: str | None = None
    context_requirement_id: str | None = None
    kv_requirement_id: str | None = None
    dependency_segment_ids: tuple[str, ...] = ()
    required_handoff_ids: tuple[str, ...] = ()
    produced_handoff_ids: tuple[str, ...] = ()
    handoff_policy_id: str
    retry_policy_id: str
    verification_policy_id: str
    creation_sequence: int = Field(ge=1)
    execution_state: ExecutionSegmentState = ExecutionSegmentState.PLANNED

    @field_validator(
        "segment_id",
        "execution_plan_id",
        "namespace_id",
        "output_contract_id",
        "handoff_policy_id",
        "retry_policy_id",
        "verification_policy_id",
    )
    @classmethod
    def validate_required_text(cls, value):
        return _nonblank(value, "segment field")

    @field_validator("model_requirement_id", "context_requirement_id", "kv_requirement_id")
    @classmethod
    def validate_optional_text(cls, value):
        if value is None:
            return None
        return _nonblank(value, "optional requirement")

    @field_validator("input_artifact_ids")
    @classmethod
    def validate_artifacts(cls, value):
        return _canonical_tuple(
            value,
            "input_artifact_ids",
            MAX_EXECUTION_ARTIFACTS_PER_SEGMENT,
        )

    @field_validator("dependency_segment_ids")
    @classmethod
    def validate_dependencies(cls, value):
        return _canonical_tuple(
            value,
            "dependency_segment_ids",
            MAX_DEPENDENCIES_PER_SEGMENT,
        )

    @field_validator("required_handoff_ids", "produced_handoff_ids")
    @classmethod
    def validate_handoffs(cls, value, info):
        return _canonical_tuple(value, info.field_name, MAX_HANDOFFS_PER_SEGMENT)

    @model_validator(mode="after")
    def reject_self_dependency(self):
        if self.segment_id in self.dependency_segment_ids:
            raise ValueError("self dependency forbidden")
        return self


class ExecutionHandoff(ContractModel):
    handoff_id: str
    execution_plan_id: str
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    producer_segment_id: str
    consumer_segment_id: str
    handoff_kind: ExecutionHandoffKind
    payload_reference: str | None = None
    payload_fingerprint: str | None = None
    authorization_scope: str
    compatibility_contract_id: str
    verification_contract_id: str
    state: ExecutionHandoffState = ExecutionHandoffState.PENDING
    creation_sequence: int = Field(ge=1)
    invalidation_reason: str | None = None

    @field_validator(
        "handoff_id",
        "execution_plan_id",
        "namespace_id",
        "producer_segment_id",
        "consumer_segment_id",
        "authorization_scope",
        "compatibility_contract_id",
        "verification_contract_id",
    )
    @classmethod
    def validate_text(cls, value):
        return _nonblank(value, "handoff field")

    @field_validator("payload_reference", "payload_fingerprint", "invalidation_reason")
    @classmethod
    def validate_optional(cls, value):
        if value is None:
            return None
        return _nonblank(value, "optional handoff field")

    @model_validator(mode="after")
    def validate_handoff(self):
        if self.producer_segment_id == self.consumer_segment_id:
            raise ValueError("handoff producer and consumer must differ")
        if self.state is ExecutionHandoffState.INVALIDATED:
            if self.invalidation_reason is None:
                raise ValueError("invalidated handoff requires reason")
        elif self.invalidation_reason is not None:
            raise ValueError("invalidation reason only valid for invalidated handoff")
        return self


class DisaggregatedExecutionPlan(ContractModel):
    execution_plan_id: str
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    source_execution_graph_id: str
    segments: tuple[ExecutionSegment, ...]
    handoffs: tuple[ExecutionHandoff, ...] = ()
    entry_segment_ids: tuple[str, ...]
    terminal_segment_ids: tuple[str, ...]
    creation_sequence: int = Field(ge=1)
    plan_version: str
    plan_fingerprint: str

    @field_validator(
        "execution_plan_id",
        "namespace_id",
        "source_execution_graph_id",
        "plan_version",
        "plan_fingerprint",
    )
    @classmethod
    def validate_text(cls, value):
        return _nonblank(value, "plan field")

    @field_validator("entry_segment_ids", "terminal_segment_ids")
    @classmethod
    def validate_segment_sets(cls, value, info):
        return _canonical_tuple(value, info.field_name)


class SegmentExecutionResult(ContractModel):
    segment_result_id: str
    execution_plan_id: str
    segment_id: str
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    succeeded: bool
    verified: bool
    output_artifact_ids: tuple[str, ...] = ()
    failure_category: ExecutionFailureCategory | None = None
    attempt: int = Field(ge=1, le=MAX_RETRY_ATTEMPTS)
    result_fingerprint: str

    @field_validator(
        "segment_result_id",
        "execution_plan_id",
        "segment_id",
        "namespace_id",
        "result_fingerprint",
    )
    @classmethod
    def validate_text(cls, value):
        return _nonblank(value, "segment result field")

    @field_validator("output_artifact_ids")
    @classmethod
    def validate_outputs(cls, value):
        return _canonical_tuple(
            value,
            "output_artifact_ids",
            MAX_EXECUTION_ARTIFACTS_PER_SEGMENT,
        )

    @model_validator(mode="after")
    def validate_result(self):
        if self.succeeded and not self.verified:
            raise ValueError("successful segment result must be verified")
        if self.succeeded and self.failure_category is not None:
            raise ValueError("successful result cannot carry failure category")
        if not self.succeeded and self.failure_category is None:
            raise ValueError("failed result requires failure category")
        return self


class StitchedExecutionResult(ContractModel):
    stitched_result_id: str
    execution_plan_id: str
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    terminal_segment_ids: tuple[str, ...]
    terminal_result_ids: tuple[str, ...]
    artifact_lineage: tuple[str, ...]
    verification_status: bool
    stitching_policy_id: str
    result_fingerprint: str

    @field_validator(
        "stitched_result_id",
        "execution_plan_id",
        "namespace_id",
        "stitching_policy_id",
        "result_fingerprint",
    )
    @classmethod
    def validate_text(cls, value):
        return _nonblank(value, "stitched result field")

    @field_validator("terminal_segment_ids", "terminal_result_ids", "artifact_lineage")
    @classmethod
    def validate_tuples(cls, value, info):
        return _canonical_tuple(value, info.field_name)


def make_segment_id(*, execution_plan_seed: str, segment_type: ExecutionSegmentType, creation_sequence: int, namespace_type: GlobalMemoryNamespace, namespace_id: str) -> str:
    _nonblank(execution_plan_seed, "execution_plan_seed")
    _nonblank(namespace_id, "namespace_id")
    if creation_sequence < 1:
        raise ValueError("creation_sequence must be positive")
    return _stable_hash(
        {
            "execution_plan_seed": execution_plan_seed,
            "segment_type": segment_type.value,
            "creation_sequence": creation_sequence,
            "namespace_type": namespace_type.value,
            "namespace_id": namespace_id,
        }
    )


def make_handoff_id(*, execution_plan_id: str, producer_segment_id: str, consumer_segment_id: str, handoff_kind: ExecutionHandoffKind, creation_sequence: int) -> str:
    for value, field in (
        (execution_plan_id, "execution_plan_id"),
        (producer_segment_id, "producer_segment_id"),
        (consumer_segment_id, "consumer_segment_id"),
    ):
        _nonblank(value, field)
    return _stable_hash(
        {
            "execution_plan_id": execution_plan_id,
            "producer_segment_id": producer_segment_id,
            "consumer_segment_id": consumer_segment_id,
            "handoff_kind": handoff_kind.value,
            "creation_sequence": creation_sequence,
        }
    )


def make_execution_plan_id(*, namespace_type: GlobalMemoryNamespace, namespace_id: str, source_execution_graph_id: str, plan_version: str) -> str:
    _nonblank(namespace_id, "namespace_id")
    _nonblank(source_execution_graph_id, "source_execution_graph_id")
    _nonblank(plan_version, "plan_version")
    return _stable_hash(
        {
            "namespace_type": namespace_type.value,
            "namespace_id": namespace_id,
            "source_execution_graph_id": source_execution_graph_id,
            "plan_version": plan_version,
        }
    )
