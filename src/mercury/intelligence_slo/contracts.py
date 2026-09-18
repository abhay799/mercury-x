from enum import Enum
from pydantic import Field, field_validator, model_validator
from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import canonical_hash

class ConstraintKind(str,Enum):
    HARD="HARD"; SOFT="SOFT"; UNKNOWN="UNKNOWN"
class CompilationStatus(str,Enum):
    VALID="VALID"; INVALID="INVALID"; AMBIGUOUS="AMBIGUOUS"; UNSATISFIABLE="UNSATISFIABLE"

class IntelligenceRequirement(ContractModel):
    requirement_id:str; metric_id:str; kind:ConstraintKind; threshold:float|None=None
    operator:str|None=None; source_id:str; provenance_ids:tuple[str,...]=()
    @model_validator(mode="after")
    def typed_threshold(self):
        if self.kind is not ConstraintKind.UNKNOWN and (self.threshold is None or self.operator is None):
            raise ValueError("typed constraint requires threshold and operator")
        if not self.requirement_id.strip() or not self.metric_id.strip() or not self.source_id.strip():
            raise ValueError("requirement identity must be nonblank")
        return self

class ApplicationSLA(ContractModel):
    sla_id:str; workload_class:str; requirements:tuple[IntelligenceRequirement,...]
    degradation_allowed:bool=False; provenance_ids:tuple[str,...]
    @model_validator(mode="after")
    def no_degradation(self):
        if self.degradation_allowed: raise ValueError("SLA degradation cannot be enabled by compiler input")
        if not self.provenance_ids: raise ValueError("SLA provenance required")
        return self

class IntelligenceSLO(ContractModel):
    intelligence_slo_id:str; source_sla_id:str; version:int=Field(ge=1)
    previous_version_id:str|None=None; requirements:tuple[IntelligenceRequirement,...]
    degradation_allowed:bool=False; status:CompilationStatus
    hard_constraints:tuple[str,...]=(); soft_constraints:tuple[str,...]=(); unknown_constraints:tuple[str,...]=()
    provenance_ids:tuple[str,...]=(); fingerprint:str
    workload_class:str
    metric_registry_fingerprint:str
    @model_validator(mode="after")
    def integrity(self):
        if self.degradation_allowed: raise ValueError("compiled SLO cannot allow degradation")
        body={"sla":self.source_sla_id,"version":self.version,
              "requirements":[r.model_dump(mode="json") for r in self.requirements],
              "degradation_allowed":False,"status":self.status.value,
              "previous":self.previous_version_id,"workload_class":self.workload_class,
              "metric_registry_fingerprint":self.metric_registry_fingerprint}
        expected=canonical_hash(body)
        if self.fingerprint!=expected or self.intelligence_slo_id!=canonical_hash({"intelligence_slo":expected}):
            raise ValueError("intelligence SLO fingerprint mismatch")
        return self
