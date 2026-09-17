from enum import Enum
from pydantic import Field, field_validator
from mercury.contracts.base import ContractModel
from mercury.reasoning_budget.contracts import canonical_hash

class ConstraintKind(str,Enum):
    HARD="HARD"; SOFT="SOFT"; UNKNOWN="UNKNOWN"
class CompilationStatus(str,Enum):
    VALID="VALID"; INVALID="INVALID"; AMBIGUOUS="AMBIGUOUS"; UNSATISFIABLE="UNSATISFIABLE"

class IntelligenceRequirement(ContractModel):
    requirement_id:str; metric_id:str; kind:ConstraintKind; threshold:float|None=None
    operator:str|None=None; source_id:str; provenance_ids:tuple[str,...]=()

class ApplicationSLA(ContractModel):
    sla_id:str; requirements:tuple[IntelligenceRequirement,...]; degradation_allowed:bool=False

class IntelligenceSLO(ContractModel):
    intelligence_slo_id:str; source_sla_id:str; version:int=Field(ge=1)
    previous_version_id:str|None=None; requirements:tuple[IntelligenceRequirement,...]
    degradation_allowed:bool=False; status:CompilationStatus
    hard_constraints:tuple[str,...]=(); soft_constraints:tuple[str,...]=(); unknown_constraints:tuple[str,...]=()
    provenance_ids:tuple[str,...]=(); fingerprint:str
