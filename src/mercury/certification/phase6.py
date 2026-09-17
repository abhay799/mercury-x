"""Machine-readable certification for the Phase 6 baseline."""
from __future__ import annotations
from typing import Literal
from json import loads
from pathlib import Path
from pydantic import field_validator,model_validator
from mercury.contracts.base import ContractModel
REQUIRED_PHASE6_GATE_IDS=("precision_contracts","mode_vocabulary","canonical_order","profile_bound","exact_identity","registry_no_inference","int8_evidence","reduced_precision_rules","uniform_precision","mixed_precision","determinism","semantic_deduplication","result_semantics","fail_closed_behavior","no_ranking_selection","no_hardware_placement","no_scheduler_runtime","no_optimization")
class Phase6Gate(ContractModel):
 gate_id:str; passed:bool; evidence:str
 @field_validator("gate_id","evidence")
 @classmethod
 def nonblank(cls,v):
  if not v.strip(): raise ValueError("gate text must be nonblank")
  return v
class Phase6CertificationConfig(ContractModel):
 schema_version:Literal["mercury.certification.phase6/v1"]="mercury.certification.phase6/v1"; gates:tuple[Phase6Gate,...]; violations:tuple[str,...]=()
 @model_validator(mode="after")
 def known_unique(self):
  ids=tuple(x.gate_id for x in self.gates)
  if len(ids)!=len(set(ids)): raise ValueError("gate ids must be unique")
  if any(x not in REQUIRED_PHASE6_GATE_IDS for x in ids): raise ValueError("unknown Phase 6 certification gate")
  return self
class Phase6CertificationResult(ContractModel):
 overall_passed:bool; gates:tuple[Phase6Gate,...]; missing_gate_ids:tuple[str,...]; passed_gate_count:int; failed_gate_count:int; violations:tuple[str,...]
def evaluate_phase6_certification(config:Phase6CertificationConfig)->Phase6CertificationResult:
 if not isinstance(config,Phase6CertificationConfig): raise ValueError("config must be a Phase6CertificationConfig")
 by={x.gate_id:x for x in config.gates}; missing=tuple(x for x in REQUIRED_PHASE6_GATE_IDS if x not in by); gates=tuple(by[x] for x in REQUIRED_PHASE6_GATE_IDS if x in by); passed=sum(x.passed for x in gates); failed=len(gates)-passed
 return Phase6CertificationResult(overall_passed=not missing and not failed and not config.violations,gates=gates,missing_gate_ids=missing,passed_gate_count=passed,failed_gate_count=failed,violations=tuple(sorted(set(config.violations))))

def main() -> int:
 config=Phase6CertificationConfig(**loads((Path(__file__).parents[3]/"configs"/"certification"/"phase6.json").read_text(encoding="utf-8")))
 result=evaluate_phase6_certification(config)
 print("PASS" if result.overall_passed else "FAIL")
 return 0 if result.overall_passed else 1

if __name__ == "__main__": raise SystemExit(main())
