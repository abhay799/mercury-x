from mercury.platform.contracts import PlatformConfig, PlatformMode
from mercury.platform.engine import PlatformManager


def safe_research_mode():
    config = PlatformConfig(
        config_id="cfg-1",
        mode=PlatformMode.RESEARCH,
        cpu_local_demo=True,
        allow_cloud=False,
        allow_gpu=False,
        production_safe_defaults=True,
        provenance_ids=("p1",),
    )
    manager = PlatformManager()
    status = manager.validate_config(config)
    return status == "OK" and manager.demo_mode_enabled(config), "research mode stays CPU-local and safe by default"


CHECKS = {"safe_research_mode": safe_research_mode}
