import os
import platform
from typing import Protocol

from mercury.hardware_personality.contracts import (
    HardwareClass,
    HardwareDescriptor,
    HardwareEvidenceClass,
    HardwareEvidenceRecord,
    make_evidence_id,
)


class HardwareProbeBackend(Protocol):
    def probe(self, descriptor: HardwareDescriptor) -> tuple[HardwareEvidenceRecord, ...]:
        ...


def _record(
    descriptor: HardwareDescriptor,
    *,
    property_name: str,
    observed_value: str,
    sequence: int,
    source_id: str = "local-cpu-probe",
) -> HardwareEvidenceRecord:
    evidence_id, fp = make_evidence_id(
        hardware_id=descriptor.hardware_id,
        evidence_class=HardwareEvidenceClass.PROBED,
        property_name=property_name,
        source_id=source_id,
        sequence=sequence,
        generation=1,
        observed_value=observed_value,
    )
    return HardwareEvidenceRecord(
        evidence_id=evidence_id,
        hardware_id=descriptor.hardware_id,
        evidence_class=HardwareEvidenceClass.PROBED,
        property_name=property_name,
        observed_value=observed_value,
        source_id=source_id,
        probe_id=source_id,
        sequence=sequence,
        generation=1,
        verification_status=True,
        evidence_fingerprint=fp,
    )


class LocalCPUProbeBackend:
    def probe(self, descriptor: HardwareDescriptor) -> tuple[HardwareEvidenceRecord, ...]:
        if descriptor.hardware_class is not HardwareClass.CPU:
            raise ValueError("LocalCPUProbeBackend only supports CPU descriptors")

        observations = [
            ("cpu.machine", platform.machine() or "unknown"),
            ("cpu.processor", platform.processor() or "unknown"),
            ("cpu.logical_count", str(os.cpu_count() or 0)),
            ("runtime.python_implementation", platform.python_implementation()),
        ]
        records = tuple(
            _record(
                descriptor,
                property_name=property_name,
                observed_value=value,
                sequence=index,
            )
            for index, (property_name, value) in enumerate(observations, start=1)
        )
        return tuple(sorted(records, key=lambda item: (item.property_name, item.evidence_id)))
