from abc import ABC, abstractmethod
from typing import Optional

from qiskit.providers import BackendV2


class BaseProvider(ABC):
    """Base class for a provider."""

    @abstractmethod
    def get_backend(self, name: Optional[str] = None) -> BackendV2:
        """Get a backend by name."""
        pass

    @abstractmethod
    def backends(self) -> list[BackendV2]:
        """Return all backends for this provider."""
        pass
