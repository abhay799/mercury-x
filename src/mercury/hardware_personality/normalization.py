from mercury.hardware_personality.contracts import (
    HardwareClass,
    HardwareDescriptor,
    VirtualizationState,
    make_hardware_id,
)


def _norm_required(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonblank")
    return " ".join(value.strip().split())


def _norm_optional(value):
    if value is None:
        return None
    return _norm_required(value, "optional descriptor field")


def normalize_hardware_descriptor(raw) -> HardwareDescriptor:
    if isinstance(raw, HardwareDescriptor):
        source = raw.model_dump()
    elif isinstance(raw, dict):
        source = dict(raw)
    else:
        raise ValueError("hardware descriptor mapping required")

    try:
        hardware_class = source["hardware_class"]
        if not isinstance(hardware_class, HardwareClass):
            hardware_class = HardwareClass(str(hardware_class).upper())
        virtualization_state = source.get("virtualization_state", VirtualizationState.UNKNOWN)
        if not isinstance(virtualization_state, VirtualizationState):
            virtualization_state = VirtualizationState(str(virtualization_state).upper())

        vendor = _norm_required(source["vendor"], "vendor")
        architecture = _norm_required(source["architecture"], "architecture")
        device_family = _norm_required(source["device_family"], "device_family")
        device_model = _norm_required(source["device_model"], "device_model")
    except KeyError as exc:
        raise ValueError(f"missing hardware descriptor field: {exc.args[0]}") from exc

    hardware_id = make_hardware_id(
        hardware_class=hardware_class,
        vendor=vendor,
        architecture=architecture,
        device_family=device_family,
        device_model=device_model,
    )

    return HardwareDescriptor(
        hardware_id=hardware_id,
        hardware_class=hardware_class,
        vendor=vendor,
        architecture=architecture,
        device_family=device_family,
        device_model=device_model,
        memory_capacity_bytes=source.get("memory_capacity_bytes"),
        provider_id=_norm_optional(source.get("provider_id")),
        region_id=_norm_optional(source.get("region_id")),
        instance_type=_norm_optional(source.get("instance_type")),
        virtualization_state=virtualization_state,
    )


def make_hardware_identity(descriptor: HardwareDescriptor) -> str:
    return make_hardware_id(
        hardware_class=descriptor.hardware_class,
        vendor=descriptor.vendor,
        architecture=descriptor.architecture,
        device_family=descriptor.device_family,
        device_model=descriptor.device_model,
    )
