from mercury.global_memory.contracts import *
from mercury.global_memory.promotion import evaluate_global_promotion
from mercury.session_memory.contracts import *
def source(**u):
 v=dict(session_id="s",task_id="t",turn_id="u",record_id="sha256:"+"0"*64,record_version=1,source_phase="p",source_artifact_id="a",memory_type=SessionMemoryType.OBSERVATION,scope=SessionMemoryScope.SESSION,creation_sequence=1,lifecycle=SessionMemoryLifecycle.ACTIVE,provenance=("e",));v.update(u);return SessionMemoryRecord(**v)
def request(**u):
 v=dict(namespace_type=GlobalMemoryNamespace.PROJECT,namespace_id="n",authorized_namespace_type=GlobalMemoryNamespace.PROJECT,authorized_namespace_id="n",source_phase8_record_ids=("sha256:"+"0"*64,),promotion_policy_id="p",retention_policy_id="r",memory_type=GlobalMemoryType.PROJECT_CONTEXT,context_key="k",source_session_id="s",promotable=True);v.update(u);return GlobalPromotionRequest(**v)
def test_explicit_authorized_source_promotion_is_ready(): assert evaluate_global_promotion(request(),(source(),)).status is GlobalMemoryPhaseStatus.READY
def test_namespace_mismatch_or_nonpromotable_fails_closed():
 assert evaluate_global_promotion(request(authorized_namespace_id="other"),(source(),)).status is GlobalMemoryPhaseStatus.FAIL
 assert evaluate_global_promotion(request(promotable=False),(source(),)).status is GlobalMemoryPhaseStatus.NOT_APPLICABLE
