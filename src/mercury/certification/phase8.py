from json import loads
from pathlib import Path
from pydantic import field_validator,model_validator
from mercury.contracts.base import ContractModel
REQUIRED_PHASE8_GATE_IDS=("contracts","memory_types","scopes","lifecycle","statuses","record_limit","retrieval_limit","compaction_limit","identity","isolation","secret_admission","closure_writes","closure_determinism","active_retrieval","retrieval_order","compaction_traceability","compaction_isolation","transition_matrix","closure_mutation","forbidden_scopes","no_semantic_search","no_selection","no_runtime","no_long_term_retention","integration")
class Phase8Gate(ContractModel):
 gate_id:str; passed:bool; evidence:str
 @field_validator("gate_id","evidence")
 @classmethod
 def text(cls,v):
  if not v.strip(): raise ValueError("nonblank gate text required")
  return v
class Phase8CertificationConfig(ContractModel):
 gates:tuple[Phase8Gate,...]
 @model_validator(mode="after")
 def valid(self):
  ids=[x.gate_id for x in self.gates]
  if len(ids)!=len(set(ids)): raise ValueError("duplicate gate")
  if any(x not in REQUIRED_PHASE8_GATE_IDS for x in ids): raise ValueError("unknown gate")
  return self
class Phase8CertificationResult(ContractModel): overall_passed:bool; passed_gate_count:int; failed_gate_count:int; missing_gate_ids:tuple[str,...]
def evaluate_phase8_certification(config):
 if not isinstance(config,Phase8CertificationConfig): raise ValueError("config required")
 by={x.gate_id:x for x in config.gates}; missing=tuple(x for x in REQUIRED_PHASE8_GATE_IDS if x not in by); failed=sum(not x.passed for x in config.gates)
 return Phase8CertificationResult(overall_passed=not missing and not failed,passed_gate_count=sum(x.passed for x in config.gates),failed_gate_count=failed,missing_gate_ids=missing)
def main():
 result=evaluate_phase8_certification(Phase8CertificationConfig(**loads((Path(__file__).parents[3]/"configs"/"certification"/"phase8.json").read_text()))); print("PASS" if result.overall_passed else "FAIL"); return 0 if result.overall_passed else 1
if __name__=="__main__": raise SystemExit(main())
