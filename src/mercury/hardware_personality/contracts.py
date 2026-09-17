import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import Field, field_validator, model_validator

from mercury.contracts.base import ContractModel


class HardwareClass(str, Enum):
    CPU = "CPU"
    GPU = "GPU"
    TPU = "TPU"
    NPU = "NPU"
    OTHER_ACCELERATOR = "OTHER_ACCELERATOR"


class HardwareEvidenceClass(str, Enum):
    DECLARED = "DECLARED"
    PROBED = "PROBED"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"


class HardwareTrustState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    STALE = "STALE"
    INVALID = "INVALID"


class CapabilitySupportState(str, Enum):
    CAPABLE = "CAPABLE"
    INCAPABLE = "INCAPABLE"
    UNKNOWN = "UNKNOWN"


class HardwarePrecision(str, Enum):
    FP32 = "FP32"
    TF32 = "TF32"
    FP16 = "FP16"
    BF16 = "BF16"
    FP8 = "FP8"
    INT8 = "INT8"
    INT4 = "INT4"


class HardwareAffinityDimension(str, Enum):
    PREFILL_AFFINITY = "PREFILL_AFFINITY"
    DECODE_AFFINITY = "DECODE_AFFINITY"
    EMBEDDING_AFFINITY = "EMBEDDING_AFFINITY"
    TRAINING_AFFINITY = "TRAINING_AFFINITY"
    FINE_TUNING_AFFINITY = "FINE_TUNING_AFFINITY"
    RETRIEVAL_AFFINITY = "RETRIEVAL_AFFINITY"
    TOOL_WORKLOAD_AFFINITY = "TOOL_WORKLOAD_AFFINITY"
    MEMORY_INTENSITY_TOLERANCE = "MEMORY_INTENSITY_TOLERANCE"
    COMMUNICATION_INTENSITY_TOLERANCE = "COMMUNICATION_INTENSITY_TOLERANCE"


class HardwareAffinityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class HardwareCompatibilityState(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


class VirtualizationState(str, Enum):
    BARE_METAL = "BARE_METAL"
    VIRTUAL_MACHINE = "VIRTUAL_MACHINE"
    CONTAINERIZED = "CONTAINERIZED"
    PARTITIONED_ACCELERATOR = "PARTITIONED_ACCELERATOR"
    UNKNOWN = "UNKNOWN"


class HardwareMeasurementContext(ContractModel):
    context_id: str
    benchmark_id: str
    benchmark_version: str
    runtime_applicable: bool
    runtime_id: str | None = None
    runtime_version: str | None = None
    driver_applicable: bool
    driver_id: str | None = None
    driver_version: str | None = None
    software_stack_applicable: bool
    software_stack_id: str | None = None
    software_stack_version: str | None = None
    precision_applicable: bool
    precision_mode: HardwarePrecision | None = None
    environment_applicable: bool
    environment_id: str | None = None
    hardware_profile_generation: int = Field(ge=1)
    evidence_generation: int = Field(ge=1)
    provenance_ids: tuple[str, ...]

    @field_validator(
        "context_id", "benchmark_id", "benchmark_version", "runtime_id", "runtime_version",
        "driver_id", "driver_version", "software_stack_id", "software_stack_version",
        "environment_id",
    )
    @classmethod
    def context_text(cls, value, info):
        return None if value is None else _nonblank(value, info.field_name)

    @field_validator("provenance_ids")
    @classmethod
    def context_provenance(cls, value):
        result = _canonical_strings(value, "provenance_ids")
        if not result:
            raise ValueError("measurement context requires provenance")
        return result

    @model_validator(mode="after")
    def validate_applicability_and_identity(self):
        pairs = (
            ("runtime", self.runtime_applicable, self.runtime_id, self.runtime_version),
            ("driver", self.driver_applicable, self.driver_id, self.driver_version),
            ("software_stack", self.software_stack_applicable, self.software_stack_id, self.software_stack_version),
        )
        for name, applicable, identity, version in pairs:
            if applicable != (identity is not None and version is not None):
                raise ValueError(f"{name} applicability does not match identity/version")
        if self.precision_applicable != (self.precision_mode is not None):
            raise ValueError("precision applicability does not match precision_mode")
        if self.environment_applicable != (self.environment_id is not None):
            raise ValueError("environment applicability does not match environment_id")
        expected = make_measurement_context_id(**{
            key: value for key, value in self.model_dump().items() if key != "context_id"
        })
        if self.context_id != expected:
            raise ValueError("measurement context identity mismatch")
        return self


def _nonblank(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonblank")
    return value.strip()


def _canonical_strings(values, field: str) -> tuple[str, ...]:
    result = tuple(values)
    for item in result:
        _nonblank(item, field)
    if len(result) != len(set(result)):
        raise ValueError(f"{field} contains duplicates")
    if result != tuple(sorted(result)):
        raise ValueError(f"{field} must be canonical")
    return result


def _stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class HardwareDescriptor(ContractModel):
    hardware_id: str
    hardware_class: HardwareClass
    vendor: str
    architecture: str
    device_family: str
    device_model: str
    memory_capacity_bytes: int | None = Field(default=None, ge=1)
    provider_id: str | None = None
    region_id: str | None = None
    instance_type: str | None = None
    virtualization_state: VirtualizationState = VirtualizationState.UNKNOWN

    @field_validator("hardware_id", "vendor", "architecture", "device_family", "device_model")
    @classmethod
    def required_text(cls, value, info):
        return _nonblank(value, info.field_name)

    @field_validator("provider_id", "region_id", "instance_type")
    @classmethod
    def optional_text(cls, value, info):
        if value is None:
            return None
        return _nonblank(value, info.field_name)

    @model_validator(mode="after")
    def validate_hardware_identity(self):
        expected = make_hardware_id(
            hardware_class=self.hardware_class,
            vendor=self.vendor,
            architecture=self.architecture,
            device_family=self.device_family,
            device_model=self.device_model,
        )
        if self.hardware_id != expected:
            raise ValueError("hardware_id does not match canonical hardware identity")
        return self


class HardwareEvidenceRecord(ContractModel):
    evidence_id: str
    hardware_id: str
    evidence_class: HardwareEvidenceClass
    property_name: str
    declared_value: str | None = None
    observed_value: str | None = None
    unit: str | None = None
    source_id: str
    probe_id: str | None = None
    benchmark_id: str | None = None
    sequence: int = Field(ge=1)
    generation: int = Field(ge=1)
    verification_status: bool
    evidence_fingerprint: str
    derived_from_evidence_ids: tuple[str, ...] = ()
    measurement_context: HardwareMeasurementContext | None = None

    @field_validator("evidence_id", "hardware_id", "property_name", "source_id", "evidence_fingerprint")
    @classmethod
    def required_text(cls, value, info):
        return _nonblank(value, info.field_name)

    @field_validator("declared_value", "observed_value", "unit", "probe_id", "benchmark_id")
    @classmethod
    def optional_text(cls, value, info):
        if value is None:
            return None
        return _nonblank(value, info.field_name)

    @field_validator("derived_from_evidence_ids")
    @classmethod
    def derived_sources(cls, value):
        return _canonical_strings(value, "derived_from_evidence_ids")

    @model_validator(mode="after")
    def validate_evidence_shape(self):
        if self.evidence_class is HardwareEvidenceClass.DECLARED:
            if self.declared_value is None:
                raise ValueError("DECLARED evidence requires declared_value")
            if self.observed_value is not None:
                raise ValueError("DECLARED evidence must not include observed_value")
        elif self.evidence_class in (HardwareEvidenceClass.PROBED, HardwareEvidenceClass.MEASURED):
            if self.observed_value is None:
                raise ValueError(f"{self.evidence_class.value} evidence requires observed_value")
        elif self.evidence_class is HardwareEvidenceClass.DERIVED:
            if self.observed_value is None:
                raise ValueError("DERIVED evidence requires observed_value")
            if not self.derived_from_evidence_ids:
                raise ValueError("DERIVED evidence requires source evidence lineage")
        elif self.derived_from_evidence_ids:
            raise ValueError("only DERIVED evidence may include source evidence lineage")
        if self.evidence_class is HardwareEvidenceClass.MEASURED and self.benchmark_id is None:
            raise ValueError("MEASURED evidence requires benchmark_id")
        if self.evidence_class is HardwareEvidenceClass.MEASURED:
            if self.measurement_context is None:
                raise ValueError("MEASURED evidence requires measurement context")
            if self.benchmark_id != self.measurement_context.benchmark_id:
                raise ValueError("measurement context benchmark mismatch")
            if self.generation != self.measurement_context.evidence_generation:
                raise ValueError("measurement context generation mismatch")
        elif self.measurement_context is not None:
            raise ValueError("measurement context is only valid for MEASURED evidence")
        if self.evidence_class is HardwareEvidenceClass.PROBED and self.probe_id is None:
            raise ValueError("PROBED evidence requires probe_id")
        expected_id, expected_fingerprint = make_evidence_id(
            hardware_id=self.hardware_id,
            evidence_class=self.evidence_class,
            property_name=self.property_name,
            source_id=self.source_id,
            sequence=self.sequence,
            generation=self.generation,
            declared_value=self.declared_value,
            observed_value=self.observed_value,
            derived_from_evidence_ids=self.derived_from_evidence_ids,
            measurement_context=self.measurement_context,
        )
        if self.evidence_id != expected_id or self.evidence_fingerprint != expected_fingerprint:
            raise ValueError("evidence identity does not match evidence content")
        return self


class CapabilityAssessment(ContractModel):
    property_name: str
    support_state: CapabilitySupportState
    evidence_record_ids: tuple[str, ...] = ()
    conflict: bool = False
    conflict_reason: str | None = None

    @field_validator("property_name")
    @classmethod
    def property_text(cls, value):
        return _nonblank(value, "property_name")

    @field_validator("evidence_record_ids")
    @classmethod
    def evidence_ids(cls, value):
        return _canonical_strings(value, "evidence_record_ids")

    @model_validator(mode="after")
    def conflict_shape(self):
        if self.conflict and not self.conflict_reason:
            raise ValueError("conflict requires reason")
        if not self.conflict and self.conflict_reason is not None:
            raise ValueError("conflict_reason requires conflict")
        return self


class HardwareWorkloadAffinity(ContractModel):
    dimension: HardwareAffinityDimension
    level: HardwareAffinityLevel
    evidence_record_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()

    @field_validator("evidence_record_ids", "reason_codes")
    @classmethod
    def canonical(cls, value, info):
        return _canonical_strings(value, info.field_name)


class HardwarePersonalityProfile(ContractModel):
    hardware_profile_id: str
    descriptor: HardwareDescriptor
    capabilities: tuple[CapabilityAssessment, ...]
    supported_precisions: tuple[HardwarePrecision, ...]
    declared_memory_bandwidth_bytes_per_s: int | None = Field(default=None, ge=1)
    measured_memory_bandwidth_bytes_per_s: int | None = Field(default=None, ge=1)
    interconnect_capabilities: tuple[str, ...] = ()
    runtime_capabilities: tuple[str, ...] = ()
    software_stack: tuple[str, ...] = ()
    power_constraints: tuple[str, ...] = ()
    evidence_record_ids: tuple[str, ...]
    workload_affinities: tuple[HardwareWorkloadAffinity, ...]
    profile_generation: int = Field(ge=1)
    profile_fingerprint: str
    trust_state: HardwareTrustState

    @field_validator("hardware_profile_id", "profile_fingerprint")
    @classmethod
    def required_text(cls, value, info):
        return _nonblank(value, info.field_name)

    @field_validator(
        "interconnect_capabilities",
        "runtime_capabilities",
        "software_stack",
        "power_constraints",
        "evidence_record_ids",
    )
    @classmethod
    def canonical_strings(cls, value, info):
        return _canonical_strings(value, info.field_name)

    @field_validator("supported_precisions")
    @classmethod
    def canonical_precisions(cls, value):
        result = tuple(value)
        if len(result) != len(set(result)):
            raise ValueError("supported_precisions contains duplicates")
        if tuple(sorted(x.value for x in result)) != tuple(x.value for x in result):
            raise ValueError("supported_precisions must be canonical")
        return result

    @field_validator("capabilities")
    @classmethod
    def canonical_capabilities(cls, value):
        result = tuple(value)
        names = tuple(item.property_name for item in result)
        if len(names) != len(set(names)):
            raise ValueError("duplicate capability")
        if names != tuple(sorted(names)):
            raise ValueError("capabilities must be canonical")
        return result

    @field_validator("workload_affinities")
    @classmethod
    def canonical_affinities(cls, value):
        result = tuple(value)
        names = tuple(item.dimension.value for item in result)
        if len(names) != len(set(names)):
            raise ValueError("duplicate workload affinity")
        if names != tuple(sorted(names)):
            raise ValueError("workload_affinities must be canonical")
        return result

    @model_validator(mode="after")
    def validate_profile_integrity(self):
        expected_id = make_profile_identity(
            hardware_id=self.descriptor.hardware_id,
            profile_generation=self.profile_generation,
        )
        if self.hardware_profile_id != expected_id:
            raise ValueError("hardware_profile_id does not match descriptor identity and generation")
        if self.trust_state is HardwareTrustState.VERIFIED and not self.evidence_record_ids:
            raise ValueError("VERIFIED profile requires evidence")
        if self.profile_fingerprint != make_hardware_profile_fingerprint(
            hardware_profile_id=self.hardware_profile_id,
            descriptor=self.descriptor,
            capabilities=self.capabilities,
            supported_precisions=self.supported_precisions,
            declared_memory_bandwidth_bytes_per_s=self.declared_memory_bandwidth_bytes_per_s,
            measured_memory_bandwidth_bytes_per_s=self.measured_memory_bandwidth_bytes_per_s,
            interconnect_capabilities=self.interconnect_capabilities,
            runtime_capabilities=self.runtime_capabilities,
            software_stack=self.software_stack,
            power_constraints=self.power_constraints,
            evidence_record_ids=self.evidence_record_ids,
            workload_affinities=self.workload_affinities,
            profile_generation=self.profile_generation,
            trust_state=self.trust_state,
        ):
            raise ValueError("profile_fingerprint does not match profile content")
        return self


class HardwareRequirement(ContractModel):
    requirement_id: str
    required_hardware_class: HardwareClass | None = None
    required_precision: HardwarePrecision | None = None
    minimum_memory_bytes: int | None = Field(default=None, ge=1)
    required_runtime_capability: str | None = None
    requires_accelerator: bool | None = None
    forbidden_virtualization_states: tuple[VirtualizationState, ...] = ()

    @field_validator("requirement_id")
    @classmethod
    def required_id(cls, value):
        return _nonblank(value, "requirement_id")

    @field_validator("required_runtime_capability")
    @classmethod
    def optional_runtime(cls, value):
        if value is None:
            return None
        return _nonblank(value, "required_runtime_capability")


class HardwareCompatibilityResult(ContractModel):
    requirement_id: str
    hardware_profile_id: str
    state: HardwareCompatibilityState
    reason_codes: tuple[str, ...]

    @field_validator("requirement_id", "hardware_profile_id")
    @classmethod
    def ids(cls, value, info):
        return _nonblank(value, info.field_name)

    @field_validator("reason_codes")
    @classmethod
    def reasons(cls, value):
        return _canonical_strings(value, "reason_codes")


def make_hardware_id(*, hardware_class: HardwareClass, vendor: str, architecture: str, device_family: str, device_model: str) -> str:
    return _stable_hash(
        {
            "hardware_class": hardware_class.value,
            "vendor": _nonblank(vendor, "vendor").lower(),
            "architecture": _nonblank(architecture, "architecture").lower(),
            "device_family": _nonblank(device_family, "device_family").lower(),
            "device_model": _nonblank(device_model, "device_model").lower(),
        }
    )


def make_evidence_id(
    *,
    hardware_id: str,
    evidence_class: HardwareEvidenceClass,
    property_name: str,
    source_id: str,
    sequence: int,
    generation: int,
    declared_value: str | None = None,
    observed_value: str | None = None,
    derived_from_evidence_ids: tuple[str, ...] = (),
    measurement_context: HardwareMeasurementContext | None = None,
) -> tuple[str, str]:
    payload = {
        "hardware_id": _nonblank(hardware_id, "hardware_id"),
        "evidence_class": evidence_class.value,
        "property_name": _nonblank(property_name, "property_name"),
        "source_id": _nonblank(source_id, "source_id"),
        "sequence": sequence,
        "generation": generation,
        "declared_value": declared_value,
        "observed_value": observed_value,
        "derived_from_evidence_ids": list(
            _canonical_strings(derived_from_evidence_ids, "derived_from_evidence_ids")
        ),
        "measurement_context": measurement_context.model_dump(mode="json") if measurement_context else None,
    }
    fingerprint = _stable_hash(payload)
    return fingerprint, fingerprint


def make_measurement_context_id(**values) -> str:
    keys = (
        "benchmark_id", "benchmark_version", "runtime_applicable", "runtime_id", "runtime_version",
        "driver_applicable", "driver_id", "driver_version", "software_stack_applicable",
        "software_stack_id", "software_stack_version", "precision_applicable", "precision_mode",
        "environment_applicable", "environment_id", "hardware_profile_generation",
        "evidence_generation", "provenance_ids",
    )
    normalized = {key: values.get(key) for key in keys}
    normalized["precision_mode"] = (
        normalized["precision_mode"].value
        if isinstance(normalized.get("precision_mode"), HardwarePrecision)
        else normalized.get("precision_mode")
    )
    normalized["provenance_ids"] = list(
        _canonical_strings(tuple(normalized.get("provenance_ids") or ()), "provenance_ids")
    )
    return _stable_hash(normalized)


def make_profile_identity(*, hardware_id: str, profile_generation: int) -> str:
    if profile_generation < 1:
        raise ValueError("profile_generation must be positive")
    return _stable_hash(
        {
            "hardware_id": _nonblank(hardware_id, "hardware_id"),
            "profile_generation": profile_generation,
        }
    )


def make_hardware_profile_fingerprint(
    *,
    hardware_profile_id: str,
    descriptor: HardwareDescriptor,
    capabilities: tuple[CapabilityAssessment, ...],
    supported_precisions: tuple[HardwarePrecision, ...],
    declared_memory_bandwidth_bytes_per_s: int | None,
    measured_memory_bandwidth_bytes_per_s: int | None,
    interconnect_capabilities: tuple[str, ...],
    runtime_capabilities: tuple[str, ...],
    software_stack: tuple[str, ...],
    power_constraints: tuple[str, ...],
    evidence_record_ids: tuple[str, ...],
    workload_affinities: tuple[HardwareWorkloadAffinity, ...],
    profile_generation: int,
    trust_state: HardwareTrustState,
) -> str:
    """Return the deterministic integrity fingerprint for a logical profile."""
    return _stable_hash(
        {
            "hardware_profile_id": hardware_profile_id,
            "descriptor": descriptor.model_dump(mode="json"),
            "capabilities": [item.model_dump(mode="json") for item in capabilities],
            "supported_precisions": [item.value for item in supported_precisions],
            "declared_memory_bandwidth_bytes_per_s": declared_memory_bandwidth_bytes_per_s,
            "measured_memory_bandwidth_bytes_per_s": measured_memory_bandwidth_bytes_per_s,
            "interconnect_capabilities": list(interconnect_capabilities),
            "runtime_capabilities": list(runtime_capabilities),
            "software_stack": list(software_stack),
            "power_constraints": list(power_constraints),
            "evidence_record_ids": list(evidence_record_ids),
            "workload_affinities": [item.model_dump(mode="json") for item in workload_affinities],
            "profile_generation": profile_generation,
            "trust_state": trust_state.value,
        }
    )
