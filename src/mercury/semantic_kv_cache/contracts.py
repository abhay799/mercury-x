import hashlib
import json
from enum import Enum

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.global_memory.contracts import GlobalMemoryNamespace


MAX_KV_CACHE_ENTRIES_PER_NAMESPACE = 4096
MAX_CACHE_LOOKUP_RESULTS = 64
MAX_SOURCE_RECORDS_PER_CACHE_ENTRY = 128
MAX_CACHE_DEPENDENCIES = 64
MAX_CACHE_METADATA_BYTES = 65536


class SemanticKVReuseMode(str, Enum):
    EXACT = "EXACT"
    SEMANTIC_COMPATIBLE = "SEMANTIC_COMPATIBLE"
    NO_REUSE = "NO_REUSE"


class SemanticKVCacheState(str, Enum):
    ACTIVE = "ACTIVE"
    STALE = "STALE"
    INVALIDATED = "INVALIDATED"


def _nonblank(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _canonical_text_tuple(values, *, field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _nonblank(value, field_name=field_name)
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicates")
    if result != tuple(sorted(result)):
        raise ValueError(f"{field_name} must use canonical order")
    return result


def _stable_hash(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class SemanticKVPayloadReference(ContractModel):
    payload_backend: str
    payload_reference: str
    payload_fingerprint: str
    payload_size_bytes: int = Field(ge=1)

    @field_validator(
        "payload_backend",
        "payload_reference",
        "payload_fingerprint",
    )
    @classmethod
    def validate_text(cls, value):
        return _nonblank(value, field_name="payload field")


class SemanticKVCacheEntry(ContractModel):
    cache_entry_id: str
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    cache_generation: int = Field(ge=1)
    semantic_key: str
    semantic_fingerprint: str

    model_id: str | None = None
    model_version: str | None = None
    tokenizer_id: str | None = None
    attention_layout: str | None = None
    kv_format: str | None = None
    precision: str | None = None
    context_generation: int = Field(default=1, ge=1)

    source_phase8_record_ids: tuple[str, ...] = ()
    source_global_record_ids: tuple[str, ...] = ()
    source_prediction_ids: tuple[str, ...] = ()
    source_artifact_ids: tuple[str, ...] = ()
    dependency_cache_entry_ids: tuple[str, ...] = ()

    payload: SemanticKVPayloadReference | None = None

    state: SemanticKVCacheState = SemanticKVCacheState.ACTIVE
    creation_sequence: int = Field(ge=1)
    invalidation_reason: str | None = None

    @field_validator(
        "cache_entry_id",
        "namespace_id",
        "semantic_key",
        "semantic_fingerprint",
    )
    @classmethod
    def validate_required_text(cls, value):
        return _nonblank(value, field_name="cache entry field")

    @field_validator(
        "model_id",
        "model_version",
        "tokenizer_id",
        "attention_layout",
        "kv_format",
        "precision",
        "invalidation_reason",
    )
    @classmethod
    def validate_optional_text(cls, value):
        if value is None:
            return None
        return _nonblank(value, field_name="optional cache entry field")

    @field_validator(
        "source_phase8_record_ids",
        "source_global_record_ids",
        "source_prediction_ids",
        "source_artifact_ids",
        "dependency_cache_entry_ids",
    )
    @classmethod
    def validate_canonical_tuples(cls, value, info):
        return _canonical_text_tuple(value, field_name=info.field_name)

    @model_validator(mode="after")
    def validate_entry(self):
        source_count = (
            len(self.source_phase8_record_ids)
            + len(self.source_global_record_ids)
            + len(self.source_prediction_ids)
        )
        if source_count > MAX_SOURCE_RECORDS_PER_CACHE_ENTRY:
            raise ValueError("too many source records per cache entry")
        if len(self.dependency_cache_entry_ids) > MAX_CACHE_DEPENDENCIES:
            raise ValueError("too many cache dependencies")

        physical_fields = (
            self.model_id,
            self.model_version,
            self.tokenizer_id,
            self.attention_layout,
            self.kv_format,
            self.precision,
        )
        if self.payload is not None and any(value is None for value in physical_fields):
            raise ValueError(
                "physical payload requires complete model/tokenizer/KV compatibility metadata"
            )
        if self.state is SemanticKVCacheState.INVALIDATED:
            if self.invalidation_reason is None:
                raise ValueError("invalidated entry requires invalidation reason")
        elif self.invalidation_reason is not None:
            raise ValueError("invalidation reason only valid for invalidated entries")
        return self


class SemanticKVLookupRequest(ContractModel):
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    authorized_namespace_type: GlobalMemoryNamespace
    authorized_namespace_id: str

    semantic_key: str
    semantic_fingerprint: str | None = None

    model_id: str | None = None
    model_version: str | None = None
    tokenizer_id: str | None = None
    attention_layout: str | None = None
    kv_format: str | None = None
    precision: str | None = None
    context_generation: int = Field(default=1, ge=1)

    limit: int = Field(default=MAX_CACHE_LOOKUP_RESULTS, ge=1, le=MAX_CACHE_LOOKUP_RESULTS)

    @field_validator(
        "namespace_id",
        "authorized_namespace_id",
        "semantic_key",
    )
    @classmethod
    def validate_required_text(cls, value):
        return _nonblank(value, field_name="lookup field")

    @field_validator(
        "semantic_fingerprint",
        "model_id",
        "model_version",
        "tokenizer_id",
        "attention_layout",
        "kv_format",
        "precision",
    )
    @classmethod
    def validate_optional_text(cls, value):
        if value is None:
            return None
        return _nonblank(value, field_name="lookup optional field")

    @model_validator(mode="after")
    def validate_authorization(self):
        if (
            self.namespace_type is not self.authorized_namespace_type
            or self.namespace_id != self.authorized_namespace_id
        ):
            raise ValueError("namespace authorization mismatch")
        return self


class SemanticKVCompatibilityResult(ContractModel):
    cache_entry_id: str
    reuse_mode: SemanticKVReuseMode
    semantic_reuse_allowed: bool
    physical_kv_reuse_allowed: bool
    reason_codes: tuple[str, ...] = ()

    @field_validator("cache_entry_id")
    @classmethod
    def validate_cache_entry_id(cls, value):
        return _nonblank(value, field_name="cache_entry_id")

    @field_validator("reason_codes")
    @classmethod
    def validate_reason_codes(cls, value):
        return _canonical_text_tuple(value, field_name="reason_codes")

    @model_validator(mode="after")
    def validate_decision(self):
        if self.physical_kv_reuse_allowed and not self.semantic_reuse_allowed:
            raise ValueError("physical KV reuse requires semantic reuse")
        if self.reuse_mode is SemanticKVReuseMode.NO_REUSE:
            if self.semantic_reuse_allowed or self.physical_kv_reuse_allowed:
                raise ValueError("NO_REUSE cannot allow reuse")
        return self


class SemanticKVLookupMatch(ContractModel):
    entry: SemanticKVCacheEntry
    compatibility: SemanticKVCompatibilityResult


class SemanticKVLookupResult(ContractModel):
    matches: tuple[SemanticKVLookupMatch, ...] = ()

    @field_validator("matches")
    @classmethod
    def validate_limit(cls, value):
        result = tuple(value)
        if len(result) > MAX_CACHE_LOOKUP_RESULTS:
            raise ValueError("too many cache lookup results")
        ids = tuple(match.entry.cache_entry_id for match in result)
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate cache lookup result")
        return result


def make_semantic_kv_cache_entry_id(
    *,
    namespace_type: GlobalMemoryNamespace,
    namespace_id: str,
    cache_generation: int,
    semantic_key: str,
    semantic_fingerprint: str,
    model_id: str | None,
    model_version: str | None,
    tokenizer_id: str | None,
    attention_layout: str | None,
    kv_format: str | None,
    precision: str | None,
    context_generation: int,
    source_phase8_record_ids: tuple[str, ...],
    source_global_record_ids: tuple[str, ...],
    source_prediction_ids: tuple[str, ...],
    source_artifact_ids: tuple[str, ...],
    dependency_cache_entry_ids: tuple[str, ...],
    payload: SemanticKVPayloadReference | None,
    state: SemanticKVCacheState,
    creation_sequence: int,
    invalidation_reason: str | None = None,
) -> str:
    _nonblank(namespace_id, field_name="namespace_id")
    _nonblank(semantic_key, field_name="semantic_key")
    _nonblank(semantic_fingerprint, field_name="semantic_fingerprint")

    source_phase8_record_ids = _canonical_text_tuple(
        source_phase8_record_ids,
        field_name="source_phase8_record_ids",
    )
    source_global_record_ids = _canonical_text_tuple(
        source_global_record_ids,
        field_name="source_global_record_ids",
    )
    source_prediction_ids = _canonical_text_tuple(
        source_prediction_ids,
        field_name="source_prediction_ids",
    )
    source_artifact_ids = _canonical_text_tuple(
        source_artifact_ids,
        field_name="source_artifact_ids",
    )
    dependency_cache_entry_ids = _canonical_text_tuple(
        dependency_cache_entry_ids,
        field_name="dependency_cache_entry_ids",
    )

    payload_data = None if payload is None else payload.model_dump(mode="json")

    return _stable_hash(
        {
            "namespace_type": namespace_type.value,
            "namespace_id": namespace_id,
            "cache_generation": cache_generation,
            "semantic_key": semantic_key,
            "semantic_fingerprint": semantic_fingerprint,
            "model_id": model_id,
            "model_version": model_version,
            "tokenizer_id": tokenizer_id,
            "attention_layout": attention_layout,
            "kv_format": kv_format,
            "precision": precision,
            "context_generation": context_generation,
            "source_phase8_record_ids": list(source_phase8_record_ids),
            "source_global_record_ids": list(source_global_record_ids),
            "source_prediction_ids": list(source_prediction_ids),
            "source_artifact_ids": list(source_artifact_ids),
            "dependency_cache_entry_ids": list(dependency_cache_entry_ids),
            "payload": payload_data,
            "state": state.value,
            "creation_sequence": creation_sequence,
            "invalidation_reason": invalidation_reason,
        }
    )
