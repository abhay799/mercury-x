import pytest
from mercury.global_memory.contracts import *
from mercury.global_memory.store import GlobalContextStore,register_global_context_record
def record(**u):
 v=dict(namespace_type=GlobalMemoryNamespace.PROJECT,namespace_id="n",global_record_id="sha256:"+"0"*64,record_version=1,source_session_id="s",source_phase8_record_ids=("r",),source_artifact_ids=("a",),source_phase="p",memory_type=GlobalMemoryType.VALIDATED_FACT,context_key="k",creation_sequence=1,lifecycle=GlobalMemoryLifecycle.ACTIVE,conflict_state=GlobalMemoryConflictState.CLEAR,provenance=("e",),promotion_policy_id="pp",retention_policy_id="rp");v.update(u);return GlobalContextRecord(**v)
def test_exact_namespace_registration_and_isolation():
 r=record(); store=register_global_context_record(GlobalContextStore(),r,GlobalMemoryNamespace.PROJECT,"n")
 assert store.records_for_namespace(GlobalMemoryNamespace.PROJECT,"n")== (r,)
 with pytest.raises(ValueError): store.records_for_namespace(GlobalMemoryNamespace.PROJECT,"other")
