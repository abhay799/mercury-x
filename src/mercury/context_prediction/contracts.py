import hashlib
import json
import math
from enum import Enum
from typing import Literal

from pydantic import (
    Field,
    field_validator,
    model_validator,
)

from mercury.contracts.base import ContractModel
from mercury.global_memory.contracts import (
    GlobalMemoryNamespace, GlobalMemoryConflictState,
)


MAX_PREDICTION_CANDIDATES = 256
MAX_CONTEXT_PREDICTIONS = 64
MAX_SOURCE_RECORDS_PER_PREDICTION = 128
MAX_REASON_CODES = 16


class SessionPredictionScope(ContractModel):
    """Explicit caller binding of one authorized session to the request namespace."""
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    session_id: str

    @field_validator("namespace_id", "session_id")
    @classmethod
    def nonblank(cls, value):
        return _require_nonblank(value, field_name="session scope")


class ContextPredictionSourceEvidence(ContractModel):
    source_kind: Literal["SESSION", "GLOBAL"]
    record_id: str
    record_version: int = Field(ge=1, strict=True)
    sequence_scope: str
    creation_sequence: int = Field(ge=1, strict=True)
    source_artifact_ids: tuple[str, ...]
    source_phase8_record_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...]
    conflict_state: GlobalMemoryConflictState | None = None

    @field_validator("record_id", "sequence_scope")
    @classmethod
    def text(cls, value):
        return _require_nonblank(value, field_name="source evidence")

    @field_validator("provenance", "source_artifact_ids", "source_phase8_record_ids")
    @classmethod
    def canonical(cls, value, info):
        if not value and info.field_name != "source_phase8_record_ids":
            raise ValueError("source evidence must be nonempty")
        for item in value:
            _require_nonblank(item, field_name=info.field_name)
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def source_state(self):
        if self.source_kind == "GLOBAL" and (self.conflict_state is None or not self.source_phase8_record_ids):
            raise ValueError("global source requires explicit conflict state and lineage")
        if self.source_kind == "SESSION" and self.conflict_state is not None:
            raise ValueError("session source has no global conflict state")
        return self


def canonical_source_evidence(values):
    items = tuple(ContextPredictionSourceEvidence.model_validate(item.model_dump()) for item in values)
    keys = tuple((item.source_kind, item.record_id) for item in items)
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate source evidence")
    if len(items) > MAX_SOURCE_RECORDS_PER_PREDICTION:
        raise ValueError("too many source evidence records")
    return tuple(sorted(items, key=lambda item: (item.source_kind, item.record_id)))


def validate_evidence_links(value):
    if not value.source_evidence:
        return  # Legacy identity-only contracts remain readable; execution requires evidence.
    globals_ = {item.record_id for item in value.source_evidence if item.source_kind == "GLOBAL"}
    sessions = {item.record_id for item in value.source_evidence if item.source_kind == "SESSION"}
    sessions.update(rid for item in value.source_evidence for rid in item.source_phase8_record_ids)
    if globals_ != set(value.source_global_record_ids) or sessions != set(value.source_phase8_record_ids):
        raise ValueError("source evidence does not match source identities")



class ContextPredictionHorizon(str, Enum):
    NEXT_TURN = "NEXT_TURN"
    NEXT_TASK = "NEXT_TASK"
    SESSION_NEAR_TERM = "SESSION_NEAR_TERM"


class ContextConfidenceBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ContextCalibrationStatus(str, Enum):
    UNCALIBRATED = "UNCALIBRATED"
    EMPIRICALLY_CALIBRATED = "EMPIRICALLY_CALIBRATED"


class ContextPredictionReasonCode(str, Enum):
    TASK_CONTINUITY = "TASK_CONTINUITY"
    CONTEXT_RECURRENCE = "CONTEXT_RECURRENCE"
    DEPENDENCY_ADJACENCY = "DEPENDENCY_ADJACENCY"
    SOURCE_LINEAGE_OVERLAP = (
        "SOURCE_LINEAGE_OVERLAP"
    )
    ARTIFACT_CONTINUITY = "ARTIFACT_CONTINUITY"
    SESSION_GLOBAL_AGREEMENT = (
        "SESSION_GLOBAL_AGREEMENT"
    )
    CONFLICT_PRESENT = "CONFLICT_PRESENT"
    NEAR_TERM_SESSION_SIGNAL = (
        "NEAR_TERM_SESSION_SIGNAL"
    )


def _require_nonblank(
    value: str,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be text"
        )

    if not value.strip():
        raise ValueError(
            f"{field_name} must be nonblank"
        )

    return value


def _require_canonical_text_tuple(
    values: tuple[str, ...],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(values)

    for value in normalized:
        _require_nonblank(
            value,
            field_name=field_name,
        )

    if len(normalized) != len(set(normalized)):
        raise ValueError(
            f"{field_name} must not contain duplicates"
        )

    if normalized != tuple(sorted(normalized)):
        raise ValueError(
            f"{field_name} must use canonical order"
        )

    return normalized


def _canonical_json_hash(
    payload: dict,
) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _enum_value(value):
    if isinstance(value, Enum):
        return value.value

    return value


def make_context_prediction_candidate_id(
    *,
    namespace_type: GlobalMemoryNamespace,
    namespace_id: str,
    context_key: str,
    source_global_record_ids: tuple[str, ...],
    source_phase8_record_ids: tuple[str, ...],
    source_artifact_ids: tuple[str, ...],
    conflict_present: bool,
    creation_sequence: int,
) -> str:
    _require_nonblank(
        namespace_id,
        field_name="namespace_id",
    )

    _require_nonblank(
        context_key,
        field_name="context_key",
    )

    if not isinstance(
        namespace_type,
        GlobalMemoryNamespace,
    ):
        raise ValueError(
            "namespace_type must be certified"
        )

    if not isinstance(
        creation_sequence,
        int,
    ) or isinstance(
        creation_sequence,
        bool,
    ):
        raise ValueError(
            "creation_sequence must be integer"
        )

    if creation_sequence < 1:
        raise ValueError(
            "creation_sequence must be positive"
        )

    global_ids = (
        _require_canonical_text_tuple(
            tuple(source_global_record_ids),
            field_name=(
                "source_global_record_ids"
            ),
        )
    )

    phase8_ids = (
        _require_canonical_text_tuple(
            tuple(source_phase8_record_ids),
            field_name=(
                "source_phase8_record_ids"
            ),
        )
    )

    artifact_ids = (
        _require_canonical_text_tuple(
            tuple(source_artifact_ids),
            field_name="source_artifact_ids",
        )
    )

    return _canonical_json_hash(
        {
            "namespace_type": (
                namespace_type.value
            ),
            "namespace_id": namespace_id,
            "context_key": context_key,
            "source_global_record_ids": (
                list(global_ids)
            ),
            "source_phase8_record_ids": (
                list(phase8_ids)
            ),
            "source_artifact_ids": (
                list(artifact_ids)
            ),
            "conflict_present": bool(
                conflict_present
            ),
            "creation_sequence": (
                creation_sequence
            ),
        }
    )


def make_context_prediction_id(
    *,
    namespace_type: GlobalMemoryNamespace,
    namespace_id: str,
    context_key: str,
    source_global_record_ids: tuple[str, ...],
    source_phase8_record_ids: tuple[str, ...],
    prediction_horizon: ContextPredictionHorizon,
    confidence: float,
    confidence_band: ContextConfidenceBand,
    reason_codes: tuple[
        ContextPredictionReasonCode,
        ...
    ],
    creation_sequence: int,
    predictor_id: str,
    predictor_version: str,
) -> str:
    _require_nonblank(
        namespace_id,
        field_name="namespace_id",
    )

    _require_nonblank(
        context_key,
        field_name="context_key",
    )

    _require_nonblank(
        predictor_id,
        field_name="predictor_id",
    )

    _require_nonblank(
        predictor_version,
        field_name="predictor_version",
    )

    if not isinstance(
        namespace_type,
        GlobalMemoryNamespace,
    ):
        raise ValueError(
            "namespace_type must be certified"
        )

    if not isinstance(
        prediction_horizon,
        ContextPredictionHorizon,
    ):
        raise ValueError(
            "prediction_horizon must be certified"
        )

    if not isinstance(
        confidence_band,
        ContextConfidenceBand,
    ):
        raise ValueError(
            "confidence_band must be certified"
        )

    if not isinstance(
        confidence,
        (int, float),
    ) or isinstance(
        confidence,
        bool,
    ):
        raise ValueError(
            "confidence must be numeric"
        )

    confidence_value = float(
        confidence
    )

    if not math.isfinite(
        confidence_value
    ):
        raise ValueError(
            "confidence must be finite"
        )

    if not 0.0 <= confidence_value <= 1.0:
        raise ValueError(
            "confidence must be bounded"
        )

    if not isinstance(
        creation_sequence,
        int,
    ) or isinstance(
        creation_sequence,
        bool,
    ):
        raise ValueError(
            "creation_sequence must be integer"
        )

    if creation_sequence < 1:
        raise ValueError(
            "creation_sequence must be positive"
        )

    global_ids = (
        _require_canonical_text_tuple(
            tuple(source_global_record_ids),
            field_name=(
                "source_global_record_ids"
            ),
        )
    )

    phase8_ids = (
        _require_canonical_text_tuple(
            tuple(source_phase8_record_ids),
            field_name=(
                "source_phase8_record_ids"
            ),
        )
    )

    reason_values = tuple(
        _enum_value(reason)
        for reason in reason_codes
    )

    if any(
        not isinstance(
            reason,
            ContextPredictionReasonCode,
        )
        for reason in reason_codes
    ):
        raise ValueError(
            "reason_codes must be certified"
        )

    if len(reason_values) != len(
        set(reason_values)
    ):
        raise ValueError(
            "reason_codes must not contain duplicates"
        )

    if reason_values != tuple(
        sorted(reason_values)
    ):
        raise ValueError(
            "reason_codes must use canonical order"
        )

    if len(reason_values) > MAX_REASON_CODES:
        raise ValueError(
            "too many reason codes"
        )

    return _canonical_json_hash(
        {
            "namespace_type": (
                namespace_type.value
            ),
            "namespace_id": namespace_id,
            "context_key": context_key,
            "source_global_record_ids": (
                list(global_ids)
            ),
            "source_phase8_record_ids": (
                list(phase8_ids)
            ),
            "prediction_horizon": (
                prediction_horizon.value
            ),
            "confidence": format(
                confidence_value,
                ".12f",
            ),
            "confidence_band": (
                confidence_band.value
            ),
            "reason_codes": list(
                reason_values
            ),
            "creation_sequence": (
                creation_sequence
            ),
            "predictor_id": predictor_id,
            "predictor_version": (
                predictor_version
            ),
        }
    )


class ContextPredictionCandidate(
    ContractModel
):
    namespace_type: GlobalMemoryNamespace
    namespace_id: str
    context_key: str
    candidate_id: str
    source_evidence: tuple[ContextPredictionSourceEvidence, ...] = ()

    @field_validator("source_evidence")
    @classmethod
    def evidence(cls, value):
        return canonical_source_evidence(value)

    source_global_record_ids: tuple[
        str,
        ...
    ] = ()

    source_phase8_record_ids: tuple[
        str,
        ...
    ] = ()

    source_artifact_ids: tuple[
        str,
        ...
    ] = ()

    conflict_present: bool = False

    creation_sequence: int = Field(
        ge=1
    )

    @field_validator(
        "namespace_id",
        "context_key",
        "candidate_id",
    )
    @classmethod
    def validate_text(
        cls,
        value,
    ):
        return _require_nonblank(
            value,
            field_name="text",
        )

    @field_validator(
        "source_global_record_ids",
        "source_phase8_record_ids",
        "source_artifact_ids",
    )
    @classmethod
    def validate_source_ids(
        cls,
        value,
        info,
    ):
        return (
            _require_canonical_text_tuple(
                tuple(value),
                field_name=info.field_name,
            )
        )

    @model_validator(
        mode="after"
    )
    def validate_candidate(self):
        validate_evidence_links(self)
        source_count = (
            len(
                self.source_global_record_ids
            )
            + len(
                self.source_phase8_record_ids
            )
        )

        if (
            source_count
            > MAX_SOURCE_RECORDS_PER_PREDICTION
        ):
            raise ValueError(
                "too many candidate source records"
            )

        expected_id = (
            make_context_prediction_candidate_id(
                namespace_type=(
                    self.namespace_type
                ),
                namespace_id=(
                    self.namespace_id
                ),
                context_key=self.context_key,
                source_global_record_ids=(
                    self.source_global_record_ids
                ),
                source_phase8_record_ids=(
                    self.source_phase8_record_ids
                ),
                source_artifact_ids=(
                    self.source_artifact_ids
                ),
                conflict_present=(
                    self.conflict_present
                ),
                creation_sequence=(
                    self.creation_sequence
                ),
            )
        )

        if self.candidate_id != expected_id:
            raise ValueError(
                "candidate identity mismatch"
            )

        return self


class ContextPredictionFeatureVector(
    ContractModel
):
    candidate_id: str

    recency: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    task_continuity: float = Field(
        ge=0.0,
        le=1.0,
    )

    context_key_recurrence: float = Field(
        ge=0.0,
        le=1.0,
    )

    dependency_adjacency: float = Field(
        ge=0.0,
        le=1.0,
    )

    source_lineage_overlap: float = Field(
        ge=0.0,
        le=1.0,
    )

    artifact_continuity: float = Field(
        ge=0.0,
        le=1.0,
    )

    session_global_agreement: float = Field(
        ge=0.0,
        le=1.0,
    )

    lifecycle_eligibility: float = Field(
        ge=0.0,
        le=1.0,
    )

    conflict_state: float = Field(
        ge=0.0,
        le=1.0,
    )

    horizon_compatibility: float = Field(
        ge=0.0,
        le=1.0,
    )

    @field_validator(
        "candidate_id"
    )
    @classmethod
    def validate_candidate_id(
        cls,
        value,
    ):
        return _require_nonblank(
            value,
            field_name="candidate_id",
        )

    @field_validator(
        "recency",
        "task_continuity",
        "context_key_recurrence",
        "dependency_adjacency",
        "source_lineage_overlap",
        "artifact_continuity",
        "session_global_agreement",
        "lifecycle_eligibility",
        "conflict_state",
        "horizon_compatibility",
    )
    @classmethod
    def validate_finite_feature(
        cls,
        value,
    ):
        if value is None:
            return None
        numeric = float(
            value
        )

        if not math.isfinite(
            numeric
        ):
            raise ValueError(
                "feature value must be finite"
            )

        return numeric


class ContextPrediction(
    ContractModel
):
    prediction_id: str
    source_evidence: tuple[ContextPredictionSourceEvidence, ...] = ()
    raw_score: float = Field(ge=0.0, le=1.0)
    calibration_status: ContextCalibrationStatus = ContextCalibrationStatus.UNCALIBRATED
    calibration_evidence: tuple[str, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def legacy_raw_score(cls, value):
        if isinstance(value, dict) and "raw_score" not in value and "confidence" in value:
            return dict(value, raw_score=value["confidence"])
        return value

    @field_validator("source_evidence")
    @classmethod
    def evidence(cls, value):
        return canonical_source_evidence(value)

    namespace_type: GlobalMemoryNamespace

    namespace_id: str

    context_key: str

    source_global_record_ids: tuple[
        str,
        ...
    ]

    source_phase8_record_ids: tuple[
        str,
        ...
    ]

    prediction_horizon: (
        ContextPredictionHorizon
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_band: (
        ContextConfidenceBand
    )

    reason_codes: tuple[
        ContextPredictionReasonCode,
        ...
    ]

    creation_sequence: int = Field(
        ge=1
    )

    predictor_id: str

    predictor_version: str

    @field_validator(
        "prediction_id",
        "namespace_id",
        "context_key",
        "predictor_id",
        "predictor_version",
    )
    @classmethod
    def validate_text(
        cls,
        value,
    ):
        return _require_nonblank(
            value,
            field_name="text",
        )

    @field_validator(
        "confidence"
    )
    @classmethod
    def validate_confidence(
        cls,
        value,
    ):
        numeric = float(
            value
        )

        if not math.isfinite(
            numeric
        ):
            raise ValueError(
                "confidence must be finite"
            )

        return numeric

    @field_validator(
        "source_global_record_ids",
        "source_phase8_record_ids",
    )
    @classmethod
    def validate_source_ids(
        cls,
        value,
        info,
    ):
        return (
            _require_canonical_text_tuple(
                tuple(value),
                field_name=info.field_name,
            )
        )

    @field_validator(
        "reason_codes"
    )
    @classmethod
    def validate_reason_codes(
        cls,
        value,
    ):
        values = tuple(
            value
        )

        if len(values) > MAX_REASON_CODES:
            raise ValueError(
                "too many reason codes"
            )

        reason_values = tuple(
            item.value
            for item in values
        )

        if len(reason_values) != len(
            set(reason_values)
        ):
            raise ValueError(
                "duplicate reason code"
            )

        if reason_values != tuple(
            sorted(reason_values)
        ):
            raise ValueError(
                "reason codes must use canonical order"
            )

        return values

    @model_validator(
        mode="after"
    )
    def validate_prediction(self):
        validate_evidence_links(self)
        if self.calibration_status is ContextCalibrationStatus.UNCALIBRATED:
            if self.raw_score != self.confidence or self.calibration_evidence:
                raise ValueError("uncalibrated confidence must equal raw score without empirical claims")
        elif not self.calibration_evidence:
            raise ValueError("empirical calibration requires evidence")
        _require_canonical_text_tuple(self.calibration_evidence, field_name="calibration evidence")
        expected_band = (ContextConfidenceBand.LOW if self.confidence < 0.4 else
                         ContextConfidenceBand.MEDIUM if self.confidence < 0.75 else ContextConfidenceBand.HIGH)
        if self.confidence_band is not expected_band:
            raise ValueError("confidence band inconsistent with score")
        source_count = (
            len(
                self.source_global_record_ids
            )
            + len(
                self.source_phase8_record_ids
            )
        )

        if (
            source_count
            > MAX_SOURCE_RECORDS_PER_PREDICTION
        ):
            raise ValueError(
                "too many prediction source records"
            )

        expected_id = (
            make_context_prediction_id(
                namespace_type=(
                    self.namespace_type
                ),
                namespace_id=(
                    self.namespace_id
                ),
                context_key=self.context_key,
                source_global_record_ids=(
                    self.source_global_record_ids
                ),
                source_phase8_record_ids=(
                    self.source_phase8_record_ids
                ),
                prediction_horizon=(
                    self.prediction_horizon
                ),
                confidence=self.confidence,
                confidence_band=(
                    self.confidence_band
                ),
                reason_codes=(
                    self.reason_codes
                ),
                creation_sequence=(
                    self.creation_sequence
                ),
                predictor_id=(
                    self.predictor_id
                ),
                predictor_version=(
                    self.predictor_version
                ),
            )
        )

        if self.prediction_id != expected_id:
            raise ValueError(
                "prediction identity mismatch"
            )

        return self


class ContextPredictionRequest(
    ContractModel
):
    namespace_type: GlobalMemoryNamespace
    namespace_id: str

    authorized_namespace_type: (
        GlobalMemoryNamespace
    )

    authorized_namespace_id: str

    predictor_id: str
    predictor_version: str
    prediction_horizon: ContextPredictionHorizon | None = None

    limit: int = Field(
        default=MAX_CONTEXT_PREDICTIONS,
        ge=1,
        le=MAX_CONTEXT_PREDICTIONS,
    )

    @field_validator(
        "namespace_id",
        "authorized_namespace_id",
        "predictor_id",
        "predictor_version",
    )
    @classmethod
    def validate_text(
        cls,
        value,
    ):
        return _require_nonblank(
            value,
            field_name="text",
        )

    @model_validator(
        mode="after"
    )
    def validate_authorization(self):
        if (
            self.namespace_type
            is not self.authorized_namespace_type
            or self.namespace_id
            != self.authorized_namespace_id
        ):
            raise ValueError(
                "namespace authorization mismatch"
            )

        return self


class ContextPredictionResult(
    ContractModel
):
    predictions: tuple[
        ContextPrediction,
        ...
    ] = ()

    @field_validator(
        "predictions"
    )
    @classmethod
    def validate_prediction_limit(
        cls,
        value,
    ):
        values = tuple(
            value
        )

        if len(
            values
        ) > MAX_CONTEXT_PREDICTIONS:
            raise ValueError(
                "too many predictions"
            )

        prediction_ids = tuple(
            prediction.prediction_id
            for prediction in values
        )

        if len(
            prediction_ids
        ) != len(
            set(prediction_ids)
        ):
            raise ValueError(
                "duplicate prediction"
            )

        return values
