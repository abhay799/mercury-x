from collections.abc import Iterable

from mercury.contracts.hardware_profile import HardwareProfile
from .errors import DuplicateRegistryEntryError, RegistryEntryNotFoundError


class HardwareRegistry:
    """In-memory catalog of versioned HardwareProfile records.

    Filtering represents hard capability matching only. Ranking, optimization,
    scheduling, and placement decisions are intentionally outside this class.
    """

    def __init__(self, profiles: Iterable[HardwareProfile] | None = None):
        self._profiles: dict[str, HardwareProfile] = {}
        for profile in profiles or ():
            self.register(profile)

    def register(self, profile: HardwareProfile) -> None:
        if profile.hardware_id in self._profiles:
            raise DuplicateRegistryEntryError(f"hardware_id already registered: {profile.hardware_id}")
        self._profiles[profile.hardware_id] = profile

    def get(self, hardware_id: str) -> HardwareProfile:
        try:
            return self._profiles[hardware_id]
        except KeyError as exc:
            raise RegistryEntryNotFoundError(f"hardware_id not found: {hardware_id}") from exc

    def ids(self) -> list[str]:
        return list(self._profiles.keys())

    def all(self) -> list[HardwareProfile]:
        return list(self._profiles.values())

    def find(
        self,
        *,
        hardware_type: str | None = None,
        provider: str | None = None,
        min_available_memory_gb: float | None = None,
        required_precision: str | None = None,
        evidence_type: str | None = None,
        required_label: str | None = None,
    ) -> list[HardwareProfile]:
        matches: list[HardwareProfile] = []
        for profile in self._profiles.values():
            if hardware_type is not None and profile.hardware_type != hardware_type:
                continue
            if provider is not None and profile.provider != provider:
                continue
            if min_available_memory_gb is not None and profile.available_memory_gb < min_available_memory_gb:
                continue
            if required_precision is not None and required_precision not in profile.supported_precisions:
                continue
            if evidence_type is not None and profile.evidence_type != evidence_type:
                continue
            if required_label is not None and required_label not in profile.capability_labels:
                continue
            matches.append(profile)
        return matches
