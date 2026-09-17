import pytest
from mercury.global_memory.contracts import *
def record(**u):
 v=dict(namespace_type=GlobalMemoryNamespace.PROJECT,namespace_id="n",global_record_id="sha256:"+"0"*64,record_version=1,source_session_id="s",source_phase8_record_ids=("r",),source_artifact_ids=("a",),source_phase="p",memory_type=GlobalMemoryType.VALIDATED_FACT,context_key="k",creation_sequence=1,lifecycle=GlobalMemoryLifecycle.ACTIVE,conflict_state=GlobalMemoryConflictState.CLEAR,provenance=("e",),promotion_policy_id="pp",retention_policy_id="rp");v.update(u);return GlobalContextRecord(**v)
def test_locked_vocabularies_limits_and_determinism():
 assert tuple(x.value for x in GlobalMemoryType)==("PROJECT_CONTEXT","WORKSPACE_CONTEXT","EXECUTION_KNOWLEDGE","VALIDATED_FACT","REUSABLE_ARTIFACT_CONTEXT","GLOBAL_SUMMARY")
 assert tuple(x.value for x in GlobalMemoryNamespace)==("TENANT","WORKSPACE","PROJECT")
 assert (MAX_GLOBAL_RECORDS_PER_NAMESPACE,MAX_GLOBAL_RETRIEVAL_RECORDS,MAX_PROMOTION_SOURCE_RECORDS,MAX_CONSOLIDATION_INPUT_RECORDS)==(4096,128,128,256)
 assert global_context_record_id(record())==global_context_record_id(record())
 with pytest.raises(Exception): GlobalMemoryNamespace("GLOBAL")
 with pytest.raises(Exception): record(namespace_id="")
def test_promotion_request_represents_authorized_namespace_separately():
 request=GlobalPromotionRequest(namespace_type=GlobalMemoryNamespace.PROJECT,namespace_id="target",authorized_namespace_type=GlobalMemoryNamespace.PROJECT,authorized_namespace_id="caller",source_phase8_record_ids=("r",),promotion_policy_id="p",retention_policy_id="r",memory_type=GlobalMemoryType.PROJECT_CONTEXT,context_key="k",source_session_id="s",promotable=True)
 assert request.authorized_namespace_id=="caller"
def test_query_represents_authorization_separately():
 query=GlobalMemoryQuery(namespace_type=GlobalMemoryNamespace.PROJECT,namespace_id="target",authorized_namespace_type=GlobalMemoryNamespace.PROJECT,authorized_namespace_id="caller")
 assert query.authorized_namespace_id=="caller" and query.limit==128

def test_query_supports_deterministic_structured_retrieval_filters():
 first=GlobalMemoryQuery(namespace_type=GlobalMemoryNamespace.PROJECT,namespace_id="target",authorized_namespace_type=GlobalMemoryNamespace.PROJECT,authorized_namespace_id="caller",memory_types=(GlobalMemoryType.GLOBAL_SUMMARY,GlobalMemoryType.VALIDATED_FACT),context_key="context",source_artifact_id="artifact",source_phase8_record_ids=("phase8-b","phase8-a"),record_version=2,lifecycle=GlobalMemoryLifecycle.SUPERSEDED,conflict_state=GlobalMemoryConflictState.CONFLICTING,current_only=False)
 second=GlobalMemoryQuery(namespace_type=GlobalMemoryNamespace.PROJECT,namespace_id="target",authorized_namespace_type=GlobalMemoryNamespace.PROJECT,authorized_namespace_id="caller",memory_types=(GlobalMemoryType.VALIDATED_FACT,GlobalMemoryType.GLOBAL_SUMMARY),context_key="context",source_artifact_id="artifact",source_phase8_record_ids=("phase8-a","phase8-b"),record_version=2,lifecycle=GlobalMemoryLifecycle.SUPERSEDED,conflict_state=GlobalMemoryConflictState.CONFLICTING,current_only=False)
 assert first==second
 assert first.memory_types==(GlobalMemoryType.GLOBAL_SUMMARY,GlobalMemoryType.VALIDATED_FACT)
 assert first.source_phase8_record_ids==("phase8-a","phase8-b")

def test_query_rejects_malformed_structured_retrieval_filters():
 common=dict(namespace_type=GlobalMemoryNamespace.PROJECT,namespace_id="target",authorized_namespace_type=GlobalMemoryNamespace.PROJECT,authorized_namespace_id="caller")
 with pytest.raises(Exception): GlobalMemoryQuery(**common,context_key="")
 with pytest.raises(Exception): GlobalMemoryQuery(**common,source_artifact_id="")
 with pytest.raises(Exception): GlobalMemoryQuery(**common,source_phase8_record_ids=("phase8","phase8"))
 with pytest.raises(Exception): GlobalMemoryQuery(**common,record_version=0)
