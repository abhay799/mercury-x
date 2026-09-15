class RegistryError(Exception):
    """Base error for MERCURY X registry operations."""


class DuplicateRegistryEntryError(RegistryError):
    """Raised when a registry ID is registered more than once."""


class RegistryEntryNotFoundError(RegistryError):
    """Raised when an exact registry lookup cannot find an entry."""
