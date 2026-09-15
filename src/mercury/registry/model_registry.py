from collections.abc import Iterable

from mercury.contracts.model_profile import ModelProfile
from .errors import DuplicateRegistryEntryError, RegistryEntryNotFoundError


class ModelRegistry:
    """In-memory catalog of versioned ModelProfile records.

    This registry filters declared capabilities only. It does not rank models,
    choose a winner, or make placement/scheduling decisions.
    """

    def __init__(self, profiles: Iterable[ModelProfile] | None = None):
        self._profiles: dict[str, ModelProfile] = {}
        for profile in profiles or ():
            self.register(profile)

    def register(self, profile: ModelProfile) -> None:
        if profile.model_id in self._profiles:
            raise DuplicateRegistryEntryError(f"model_id already registered: {profile.model_id}")
        self._profiles[profile.model_id] = profile

    def get(self, model_id: str) -> ModelProfile:
        try:
            return self._profiles[model_id]
        except KeyError as exc:
            raise RegistryEntryNotFoundError(f"model_id not found: {model_id}") from exc

    def ids(self) -> list[str]:
        return list(self._profiles.keys())

    def all(self) -> list[ModelProfile]:
        return list(self._profiles.values())

    def find(
        self,
        *,
        required_capabilities: set[str] | None = None,
        required_precision: str | None = None,
        provider: str | None = None,
        required_label: str | None = None,
    ) -> list[ModelProfile]:
        capabilities = required_capabilities or set()
        matches: list[ModelProfile] = []
        for profile in self._profiles.values():
            if not capabilities.issubset(set(profile.capabilities)):
                continue
            if required_precision is not None and required_precision not in profile.supported_precisions:
                continue
            if provider is not None and profile.provider != provider:
                continue
            if required_label is not None and required_label not in profile.capability_labels:
                continue
            matches.append(profile)
        return matches
