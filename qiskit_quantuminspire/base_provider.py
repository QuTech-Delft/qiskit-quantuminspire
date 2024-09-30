from abc import ABC, abstractmethod
from typing import Optional, Sequence

from qiskit.providers import BackendV2


class BaseProvider(ABC):
    """Base class for a provider."""

    @abstractmethod
    def get_backend(self, name: Optional[str] = None, id: Optional[int] = None) -> BackendV2:
        """Get a backend by name."""
        pass

    @abstractmethod
    def backends(self) -> Sequence[BackendV2]:
        """Return all backends for this provider."""
        pass
