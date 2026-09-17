import pytest
from pydantic import ValidationError

from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.contracts import (
    MAX_CACHE_DEPENDENCIES,
    MAX_CACHE_LOOKUP_RESULTS,
    MAX_CACHE_METADATA_BYTES,
    MAX_KV_CACHE_ENTRIES_PER_NAMESPACE,
    MAX_SOURCE_RECORDS_PER_CACHE_ENTRY,
    SemanticKVCacheState,
    SemanticKVLookupRequest,
    SemanticKVPayloadReference,
    SemanticKVReuseMode,
)


def test_exact_enums_and_limits():
    assert {x.value for x in SemanticKVReuseMode} == {
        "EXACT",
        "SEMANTIC_COMPATIBLE",
        "NO_REUSE",
    }
    assert {x.value for x in SemanticKVCacheState} == {
        "ACTIVE",
        "STALE",
        "INVALIDATED",
    }
    assert MAX_KV_CACHE_ENTRIES_PER_NAMESPACE == 4096
    assert MAX_CACHE_LOOKUP_RESULTS == 64
    assert MAX_SOURCE_RECORDS_PER_CACHE_ENTRY == 128
    assert MAX_CACHE_DEPENDENCIES == 64
    assert MAX_CACHE_METADATA_BYTES == 65536


def test_payload_reference_requires_complete_nonblank_identity():
    with pytest.raises(ValidationError):
        SemanticKVPayloadReference(
            payload_backend="",
            payload_reference="x",
            payload_fingerprint="y",
            payload_size_bytes=1,
        )


def test_lookup_requires_exact_namespace_authorization():
    with pytest.raises(ValidationError):
        SemanticKVLookupRequest(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="p1",
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="p2",
            semantic_key="k",
        )


def test_lookup_limit_is_bounded():
    with pytest.raises(ValidationError):
        SemanticKVLookupRequest(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="p1",
            authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
            authorized_namespace_id="p1",
            semantic_key="k",
            limit=65,
        )
