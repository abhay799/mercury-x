from mercury.global_memory.contracts import *
from mercury.session_memory.contracts import SessionMemoryRecord,SessionMemoryLifecycle
def evaluate_global_promotion(request,sources,*,classification=None):
 if not isinstance(request,GlobalPromotionRequest): raise ValueError("promotion request required")
 if not request.promotable: return GlobalPromotionResult(status=GlobalMemoryPhaseStatus.NOT_APPLICABLE,reason="promotion not explicitly requested")
 if request.namespace_type is not request.authorized_namespace_type or request.namespace_id!=request.authorized_namespace_id: return GlobalPromotionResult(status=GlobalMemoryPhaseStatus.FAIL,reason="namespace authorization mismatch")
 if not sources or len(sources)>MAX_PROMOTION_SOURCE_RECORDS or classification and classification.lower() in {"credential","password","api key","token","authentication secret","private key material"}: return GlobalPromotionResult(status=GlobalMemoryPhaseStatus.FAIL,reason="invalid promotion source")
 for source in sources:
  if not isinstance(source,SessionMemoryRecord) or source.session_id!=request.source_session_id or source.lifecycle is not SessionMemoryLifecycle.ACTIVE or not source.provenance or not source.source_artifact_id: return GlobalPromotionResult(status=GlobalMemoryPhaseStatus.FAIL,reason="ineligible source")
 return GlobalPromotionResult(status=GlobalMemoryPhaseStatus.READY,reason="explicit exact namespace promotion admitted")
