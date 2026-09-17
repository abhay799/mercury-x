from mercury.hardware_personality.contracts import (
    CapabilitySupportState,
    HardwareClass,
    HardwareCompatibilityResult,
    HardwareCompatibilityState,
    HardwarePersonalityProfile,
    HardwareRequirement,
    HardwareTrustState,
)


def evaluate_hardware_compatibility(
    profile: HardwarePersonalityProfile,
    requirement: HardwareRequirement,
) -> HardwareCompatibilityResult:
    if type(profile) is not HardwarePersonalityProfile:
        raise ValueError("HardwarePersonalityProfile required")
    if type(requirement) is not HardwareRequirement:
        raise ValueError("HardwareRequirement required")

    try:
        profile = HardwarePersonalityProfile.model_validate(profile.model_dump())
    except ValueError:
        return HardwareCompatibilityResult(
            requirement_id=requirement.requirement_id,
            hardware_profile_id=profile.hardware_profile_id,
            state=HardwareCompatibilityState.INCOMPATIBLE,
            reason_codes=("PROFILE_INTEGRITY_INVALID",),
        )

    if profile.trust_state is not HardwareTrustState.VERIFIED:
        return HardwareCompatibilityResult(
            requirement_id=requirement.requirement_id,
            hardware_profile_id=profile.hardware_profile_id,
            state=HardwareCompatibilityState.INCOMPATIBLE,
            reason_codes=("PROFILE_TRUST_NOT_VERIFIED",),
        )

    incompatible = []
    unknown = []

    if requirement.required_hardware_class is not None:
        if profile.descriptor.hardware_class is not requirement.required_hardware_class:
            incompatible.append("HARDWARE_CLASS_MISMATCH")

    if requirement.requires_accelerator is True:
        if profile.descriptor.hardware_class is HardwareClass.CPU:
            incompatible.append("ACCELERATOR_REQUIRED")

    if requirement.minimum_memory_bytes is not None:
        if profile.descriptor.memory_capacity_bytes is None:
            unknown.append("MEMORY_CAPACITY_UNKNOWN")
        elif profile.descriptor.memory_capacity_bytes < requirement.minimum_memory_bytes:
            incompatible.append("INSUFFICIENT_MEMORY")

    if requirement.required_precision is not None:
        capability = next(
            (
                item
                for item in profile.capabilities
                if item.property_name == f"precision.{requirement.required_precision.value}"
            ),
            None,
        )
        if capability is None or capability.support_state is CapabilitySupportState.UNKNOWN:
            unknown.append("PRECISION_SUPPORT_UNKNOWN")
        elif capability.support_state is CapabilitySupportState.INCAPABLE:
            incompatible.append("PRECISION_UNSUPPORTED")

    if requirement.required_runtime_capability is not None:
        capability = next(
            (
                item
                for item in profile.capabilities
                if item.property_name == requirement.required_runtime_capability
            ),
            None,
        )
        if capability is None or capability.support_state is CapabilitySupportState.UNKNOWN:
            unknown.append("RUNTIME_SUPPORT_UNKNOWN")
        elif capability.support_state is CapabilitySupportState.INCAPABLE:
            incompatible.append("RUNTIME_UNSUPPORTED")

    if profile.descriptor.virtualization_state in requirement.forbidden_virtualization_states:
        incompatible.append("VIRTUALIZATION_FORBIDDEN")

    if incompatible:
        state = HardwareCompatibilityState.INCOMPATIBLE
        reasons = tuple(sorted(set(incompatible + unknown)))
    elif unknown:
        state = HardwareCompatibilityState.UNKNOWN
        reasons = tuple(sorted(set(unknown)))
    else:
        state = HardwareCompatibilityState.COMPATIBLE
        reasons = ("ALL_EXPLICIT_REQUIREMENTS_SATISFIED",)

    return HardwareCompatibilityResult(
        requirement_id=requirement.requirement_id,
        hardware_profile_id=profile.hardware_profile_id,
        state=state,
        reason_codes=reasons,
    )


def requirement_from_phase12_segment(segment, *, explicit_requirement: HardwareRequirement | None = None) -> HardwareRequirement:
    """Bind a Phase 12 segment to an explicit Phase 13 hardware requirement.

    Phase 12 model/context requirement IDs are intentionally opaque. Phase 13
    must not invent semantics from those IDs.
    """
    from mercury.disaggregated_execution.contracts import ExecutionSegment

    if not isinstance(segment, ExecutionSegment):
        raise ValueError("Phase 12 ExecutionSegment required")

    if explicit_requirement is None:
        return HardwareRequirement(requirement_id=f"phase12:{segment.segment_id}")

    return HardwareRequirement(
        requirement_id=f"phase12:{segment.segment_id}:{explicit_requirement.requirement_id}",
        required_hardware_class=explicit_requirement.required_hardware_class,
        required_precision=explicit_requirement.required_precision,
        minimum_memory_bytes=explicit_requirement.minimum_memory_bytes,
        required_runtime_capability=explicit_requirement.required_runtime_capability,
        requires_accelerator=explicit_requirement.requires_accelerator,
        forbidden_virtualization_states=explicit_requirement.forbidden_virtualization_states,
    )
