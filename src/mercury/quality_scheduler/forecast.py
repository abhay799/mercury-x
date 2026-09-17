from typing import Protocol
from mercury.contracts.base import ContractModel
class QueueForecast(ContractModel):
    pressure:float; uncertainty:float; calibration_state:str
class QueueForecastBackend(Protocol):
    def forecast(self,queue_state)->QueueForecast: ...
class DeterministicQueueForecastBackend:
    def forecast(self,queue_state):
        n=len(queue_state)
        return QueueForecast(pressure=min(1.0,n/100.0),uncertainty=.5,calibration_state="UNCALIBRATED")
