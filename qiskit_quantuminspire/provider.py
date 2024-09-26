from abc import ABC, abstractmethod
from typing import Optional

from qiskit.providers import BackendV2 as Backend

class Provider(ABC):
    """Base class for a provider."""

    @abstractmethod
    def get_backend(self, name: Optional[str]=None) -> Backend:
        """Get a backend by name"""
        pass
    
    @abstractmethod
    def backends(self, name=None, **kwargs) -> list[Backend]:
        """Return all backends for this provider."""
        pass
