import hashlib, json
from enum import Enum
from pydantic import Field, field_validator, model_validator
from mercury.contracts.base import ContractModel

class PlacementConfidenceBand(str,Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"
class PlacementCalibrationState(str,Enum):
    UNCALIBRATED="UNCALIBRATED"; EMPIRICALLY_CALIBRATED="EMPIRICALLY_CALIBRATED"
class PlacementBackendKind(str,Enum):
    DETERMINISTIC="DETERMINISTIC"; EMPIRICAL="EMPIRICAL"; LEARNED="LEARNED"
class PlacementSupportState(str,Enum):
    SUPPORTED="SUPPORTED"; UNSUPPORTED="UNSUPPORTED"; UNKNOWN="UNKNOWN"

class PlacementCandidate(ContractModel):
    candidate_id:str; segment_id:str; topology_node_id:str; hardware_profile_id:str
    eligible:bool; reason_codes:tuple[str,...]=()
    topology_graph_id: str | None = None
    topology_generation: int | None = Field(default=None, ge=1)
    hardware_profile_generation: int | None = Field(default=None, ge=1)
    hardware_profile_fingerprint: str | None = None
    path_result_id: str | None = None
    path_result_fingerprint: str | None = None
    evidence_ids: tuple[str, ...] = ()

    @field_validator("candidate_id", "segment_id", "topology_node_id", "hardware_profile_id", "topology_graph_id", "hardware_profile_fingerprint", "path_result_id", "path_result_fingerprint")
    @classmethod
    def nonblank_ids(cls, value):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError("placement identity must be nonblank")
        return value

    @field_validator("reason_codes", "evidence_ids")
    @classmethod
    def canonical_strings(cls, values):
        values = tuple(values)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("placement strings must be nonblank")
        if len(values) != len(set(values)):
            raise ValueError("placement strings must be unique")
        return tuple(sorted(values))

    @model_validator(mode="after")
    def complete_typed_provenance(self):
        context = (
            self.topology_graph_id,
            self.topology_generation,
            self.hardware_profile_generation,
            self.hardware_profile_fingerprint,
            self.path_result_id,
            self.path_result_fingerprint,
        )
        if any(value is not None for value in context) and any(value is None for value in context):
            raise ValueError("typed placement provenance must be complete")
        if all(value is not None for value in context):
            expected = stable_hash({
                "segment_id": self.segment_id,
                "topology_graph_id": self.topology_graph_id,
                "topology_generation": self.topology_generation,
                "node_id": self.topology_node_id,
                "hardware_profile_id": self.hardware_profile_id,
                "hardware_profile_generation": self.hardware_profile_generation,
                "hardware_profile_fingerprint": self.hardware_profile_fingerprint,
                "path_result_id": self.path_result_id,
                "path_result_fingerprint": self.path_result_fingerprint,
            })
            if self.candidate_id != expected:
                raise ValueError("typed placement candidate identity mismatch")
        return self
class PlacementFeatures(ContractModel):
    candidate_id:str
    compatibility_score:float=Field(ge=0,le=1)
    locality_score:float=Field(ge=0,le=1)
    evidence_score:float=Field(ge=0,le=1)
    uncertainty_penalty:float=Field(ge=0,le=1)
    hardware_profile_id: str | None = None
    hardware_profile_generation: int | None = Field(default=None, ge=1)
    topology_graph_id: str | None = None
    topology_generation: int | None = Field(default=None, ge=1)
    path_bandwidth_bytes_per_s: int | None = Field(default=None, ge=1)
    path_latency_us: float | None = Field(default=None, gt=0)
    path_result_id: str | None = None
    path_result_fingerprint: str | None = None
    memory_headroom_bytes: int | None = Field(default=None, ge=0)
    memory_support: PlacementSupportState = PlacementSupportState.UNKNOWN
    precision_support: PlacementSupportState = PlacementSupportState.UNKNOWN
    runtime_support: PlacementSupportState = PlacementSupportState.UNKNOWN
    software_stack_support: PlacementSupportState = PlacementSupportState.UNKNOWN
    hardware_trust: PlacementSupportState = PlacementSupportState.UNKNOWN
    topology_locality: str | None = None
    path_capability: PlacementSupportState = PlacementSupportState.UNKNOWN
    topology_uncertainty: float = Field(default=1.0, ge=0, le=1)
    feature_provenance: tuple[tuple[str, tuple[str, ...]], ...] = ()
    evidence_ids: tuple[str, ...] = ()

    @field_validator("evidence_ids")
    @classmethod
    def canonical_feature_evidence(cls, values):
        values = tuple(values)
        if len(values) != len(set(values)) or any(not value.strip() for value in values):
            raise ValueError("feature evidence IDs must be unique and nonblank")
        return tuple(sorted(values))

    @field_validator("feature_provenance")
    @classmethod
    def canonical_feature_provenance(cls, values):
        normalized = tuple((name, tuple(sorted(ids))) for name, ids in values)
        if normalized != tuple(sorted(normalized, key=lambda item: item[0])):
            raise ValueError("feature provenance must be canonical")
        if len({name for name, _ in normalized}) != len(normalized):
            raise ValueError("feature provenance contains duplicate feature")
        if any(not name.strip() or any(not item.strip() for item in ids) for name, ids in normalized):
            raise ValueError("feature provenance must be nonblank")
        return normalized


class PlacementBackendResult(ContractModel):
    backend_id: str
    backend_version: str
    backend_kind: PlacementBackendKind
    candidate_id: str
    score: float = Field(ge=0, le=1)
    uncertainty: float = Field(ge=0, le=1)
    calibration_state: PlacementCalibrationState
    calibration_artifact_id: str | None = None
    calibration_dataset_id: str | None = None
    evidence_ids: tuple[str, ...] = ()
    operating_domain: str
    artifact_version: str | None = None
    hardware_profile_generation: int | None = Field(default=None, ge=1)
    topology_generation: int | None = Field(default=None, ge=1)

    @field_validator("backend_id", "backend_version", "candidate_id", "operating_domain", "calibration_artifact_id", "calibration_dataset_id", "artifact_version")
    @classmethod
    def backend_result_text(cls, value, info):
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{info.field_name} must be nonblank")
        return value

    @field_validator("evidence_ids")
    @classmethod
    def backend_evidence(cls, values):
        values = tuple(values)
        if len(values) != len(set(values)) or any(not value.strip() for value in values):
            raise ValueError("backend evidence must be unique and nonblank")
        return tuple(sorted(values))

    @model_validator(mode="after")
    def honest_calibration(self):
        if self.calibration_state is PlacementCalibrationState.EMPIRICALLY_CALIBRATED:
            if self.calibration_artifact_id is None or self.calibration_dataset_id is None or not self.evidence_ids:
                raise ValueError("empirical calibration requires artifact, dataset, and evidence")
        elif self.calibration_artifact_id is not None or self.calibration_dataset_id is not None:
            raise ValueError("uncalibrated result cannot claim calibration artifacts")
        if self.backend_kind is PlacementBackendKind.LEARNED and self.artifact_version is None:
            raise ValueError("learned backend result requires artifact version")
        return self
class PlacementPrediction(ContractModel):
    prediction_id:str; candidate_id:str; raw_score:float
    confidence_band:PlacementConfidenceBand
    calibration_state:PlacementCalibrationState=PlacementCalibrationState.UNCALIBRATED
    reason_codes:tuple[str,...]=()
    backend_id: str = "deterministic-weighted"
    backend_version: str = "v1"
    backend_kind: PlacementBackendKind = PlacementBackendKind.DETERMINISTIC
    uncertainty: float = Field(default=1.0, ge=0, le=1)
    calibration_artifact_id: str | None = None
    calibration_dataset_id: str | None = None
    evidence_ids: tuple[str, ...] = ()
    operating_domain: str = "certified-baseline"
    artifact_version: str | None = None
    hardware_profile_generation: int | None = Field(default=None, ge=1)
    topology_generation: int | None = Field(default=None, ge=1)

    @field_validator("backend_id", "backend_version")
    @classmethod
    def backend_identity(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("placement backend identity must be nonblank")
        return value

    @model_validator(mode="after")
    def prediction_calibration(self):
        PlacementBackendResult(
            backend_id=self.backend_id, backend_version=self.backend_version,
            backend_kind=self.backend_kind, candidate_id=self.candidate_id,
            score=self.raw_score, uncertainty=self.uncertainty,
            calibration_state=self.calibration_state,
            calibration_artifact_id=self.calibration_artifact_id,
            calibration_dataset_id=self.calibration_dataset_id,
            evidence_ids=self.evidence_ids, operating_domain=self.operating_domain,
            artifact_version=self.artifact_version,
            hardware_profile_generation=self.hardware_profile_generation,
            topology_generation=self.topology_generation,
        )
        return self

def stable_hash(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
