from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel


class ExecutionIdentity(ContractModel):
    request_id: str
    workload_id: str
    execution_id: str

    @field_validator("request_id", "workload_id", "execution_id")
    @classmethod
    def ids_are_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("identity ids must be non-empty")
        return value


class TraceContext(ContractModel):
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    identity: ExecutionIdentity
    node_id: str
    attempt: int = Field(ge=0)

    @field_validator("trace_id", "span_id", "parent_span_id", "node_id")
    @classmethod
    def ids_are_non_empty_when_present(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("trace ids must be non-empty")
        return value

    @model_validator(mode="after")
    def span_is_not_its_own_parent(self) -> TraceContext:
        if self.span_id == self.parent_span_id:
            raise ValueError("span cannot be its own parent")
        return self


class TraceRelation(str, Enum):
    PARENT = "parent"
    RETRY_OF = "retry_of"
    FALLBACK_FROM = "fallback_from"
    RECOMPILED_FROM = "recompiled_from"
    MIGRATED_FROM = "migrated_from"


class TraceLink(ContractModel):
    link_id: str
    relation: TraceRelation
    source_trace_id: str
    source_span_id: str
    target_trace_id: str
    target_span_id: str

    @field_validator(
        "link_id", "source_trace_id", "source_span_id", "target_trace_id", "target_span_id"
    )
    @classmethod
    def ids_are_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("trace link ids must be non-empty")
        return value

    @model_validator(mode="after")
    def does_not_link_span_to_itself(self) -> TraceLink:
        if (
            self.source_trace_id == self.target_trace_id
            and self.source_span_id == self.target_span_id
        ):
            raise ValueError("trace link cannot point a span to itself")
        return self
