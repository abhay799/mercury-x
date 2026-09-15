from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import Field
from .base import ContractModel


class RuntimeEvent(ContractModel):
    schema_version: Literal["mercury.runtime.event/v1"] = "mercury.runtime.event/v1"
    event_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    node_id: str | None = None
    event_type: str = Field(min_length=1)
    status: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict[str, Any] = Field(default_factory=dict)
