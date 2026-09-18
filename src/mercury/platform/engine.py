from mercury.platform.contracts import PlatformConfig, PlatformMode, PlatformStatus


class PlatformManager:
    def validate_config(
        self,
        config: PlatformConfig | None = None,
        *,
        mode: str | PlatformMode = PlatformMode.RESEARCH,
        cpu_local_demo: bool = True,
        allow_cloud: bool = False,
        allow_gpu: bool = False,
        production_safe_defaults: bool = True,
        provenance_ids: tuple[str, ...] = (),
    ) -> PlatformStatus | str:
        if config is None:
            config = PlatformConfig(
                config_id="default-platform-config",
                mode=PlatformMode(mode),
                cpu_local_demo=cpu_local_demo,
                allow_cloud=allow_cloud,
                allow_gpu=allow_gpu,
                production_safe_defaults=production_safe_defaults,
                provenance_ids=provenance_ids,
            )
        if config.mode is PlatformMode.RESEARCH and config.cpu_local_demo and config.production_safe_defaults:
            return PlatformStatus.OK
        if config.mode is PlatformMode.PRODUCTION and config.production_safe_defaults:
            return PlatformStatus.OK
        return PlatformStatus.FAIL

    def demo_mode_enabled(self, config: PlatformConfig | None = None, **kwargs) -> bool:
        if config is None:
            return kwargs.get("cpu_local_demo", True)
        return bool(config.cpu_local_demo)
