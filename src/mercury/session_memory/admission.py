from mercury.contracts.base import ContractModel
from mercury.session_memory.contracts import SessionMemoryRecord
class SessionMemoryAdmissionDecision(ContractModel): accepted:bool; reason:str
def evaluate_memory_admission(record,active_session_id,*,retainable,classification=None):
 if not isinstance(record,SessionMemoryRecord): return SessionMemoryAdmissionDecision(accepted=False,reason="malformed record")
 if record.session_id!=active_session_id: return SessionMemoryAdmissionDecision(accepted=False,reason="session mismatch")
 if not retainable: return SessionMemoryAdmissionDecision(accepted=False,reason="artifact is not retainable")
 if classification and classification.lower() in {"credential","password","api key","token","authentication secret","private key material"}: return SessionMemoryAdmissionDecision(accepted=False,reason="explicit secret classification")
 return SessionMemoryAdmissionDecision(accepted=True,reason="explicit retainable session-scoped record admitted")
