from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Immutable, strict base for MERCURY X versioned contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)
