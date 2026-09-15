from typing import Literal
from pydantic import Field
from .base import ContractModel


class CandidateAlternative(ContractModel):
    plan_id: str = Field(min_length=1)
    rejection_reasons: list[str] = Field(default_factory=list)


class ScheduleDecision(ContractModel):
    schema_version: Literal["mercury.schedule.decision/v1"] = "mercury.schedule.decision/v1"
    decision_id: str = Field(min_length=1)
    execution_plan_id: str = Field(min_length=1)
    selected: bool
    reasons: list[str] = Field(default_factory=list)
    alternatives: list[CandidateAlternative] = Field(default_factory=list)
