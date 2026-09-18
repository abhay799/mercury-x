from enum import Enum
from typing import Protocol
from mercury.contracts.base import ContractModel
from pydantic import Field, model_validator
class QueueForecastCalibrationState(str,Enum):
    UNCALIBRATED="UNCALIBRATED"; EMPIRICALLY_CALIBRATED="EMPIRICALLY_CALIBRATED"
class QueueForecast(ContractModel):
    pressure:float=Field(ge=0,le=1); uncertainty:float=Field(ge=0,le=1)
    calibration_state:QueueForecastCalibrationState
    backend_id:str; backend_version:str; operating_domain:str
    calibration_artifact_id:str|None=None; evidence_ids:tuple[str,...]=()
    @model_validator(mode="after")
    def honest(self):
        if self.calibration_state is QueueForecastCalibrationState.EMPIRICALLY_CALIBRATED and (not self.calibration_artifact_id or not self.evidence_ids): raise ValueError("calibration requires artifact and evidence")
        return self
class QueueForecastBackend(Protocol):
    def forecast(self,queue_state)->QueueForecast: ...
class EmpiricalQueueForecastBackend(QueueForecastBackend,Protocol): ...
class LearnedQueueForecastBackend(QueueForecastBackend,Protocol): ...
class DeterministicQueueForecastBackend:
    backend_id="deterministic-queue-pressure"; backend_version="v1"
    def forecast(self,queue_state):
        n=len(queue_state)
        return QueueForecast(pressure=min(1.0,n/100.0),uncertainty=.5,
            calibration_state=QueueForecastCalibrationState.UNCALIBRATED,
            backend_id=self.backend_id,backend_version=self.backend_version,
            operating_domain="logical-queue-count")
