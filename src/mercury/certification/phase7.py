from json import loads
from pathlib import Path
from pydantic import field_validator,model_validator
from mercury.contracts.base import ContractModel
REQUIRED_PHASE7_GATE_IDS=("contracts","dimensions","canonical_order","profile_bound","exact_lineage","registered_variants","registry_no_inference","precision_compatibility","no_cross_family","all_dimensions","determinism","semantic_dedup","result_semantics","fail_closed","no_ranking","no_hardware","no_scheduler_runtime","no_self_modification","no_optimization")
class Phase7Gate(ContractModel):
 gate_id:str; passed:bool; evidence:str
 @field_validator("gate_id","evidence")
 @classmethod
 def text(cls,v):
  if not v.strip(): raise ValueError("gate text must be nonblank")
  return v
class Phase7CertificationConfig(ContractModel):
 gates:tuple[Phase7Gate,...]
 @model_validator(mode="after")
 def valid(self):
  ids=[x.gate_id for x in self.gates]
  if len(ids)!=len(set(ids)): raise ValueError("duplicate gate id")
  if any(x not in REQUIRED_PHASE7_GATE_IDS for x in ids): raise ValueError("unknown gate")
  return self
class Phase7CertificationResult(ContractModel): overall_passed:bool; passed_gate_count:int; failed_gate_count:int; missing_gate_ids:tuple[str,...]
def evaluate_phase7_certification(config):
 if not isinstance(config,Phase7CertificationConfig): raise ValueError("config required")
 by={x.gate_id:x for x in config.gates}; missing=tuple(x for x in REQUIRED_PHASE7_GATE_IDS if x not in by); failed=sum(not x.passed for x in config.gates)
 return Phase7CertificationResult(overall_passed=not missing and not failed,passed_gate_count=sum(x.passed for x in config.gates),failed_gate_count=failed,missing_gate_ids=missing)
def main():
 config=Phase7CertificationConfig(**loads((Path(__file__).parents[3]/"configs"/"certification"/"phase7.json").read_text()))
 result=evaluate_phase7_certification(config); print("PASS" if result.overall_passed else "FAIL"); return 0 if result.overall_passed else 1
if __name__=="__main__": raise SystemExit(main())
