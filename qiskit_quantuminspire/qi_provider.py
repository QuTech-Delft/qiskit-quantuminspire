from typing import Any, List, Optional, Sequence

from compute_api_client import ApiClient, BackendType, BackendTypesApi, PageBackendType
from qi2_shared.client import config
from qi2_shared.pagination import PageReader
from qi2_shared.utils import run_async

from qiskit_quantuminspire.base_provider import BaseProvider
from qiskit_quantuminspire.qi_backend import QIBackend


class QIProvider(BaseProvider):
    """List QIBackends integrated with QiskitBackend interface."""

    def __init__(self) -> None:
        self._qiskit_backends = self._construct_backends()

    async def _fetch_qi_backend_types(self) -> List[BackendType]:
        """Fetch backend types from CJM using api client.

        (Implemented without paging only for demonstration purposes, should get a proper implementation)
        """
        async with ApiClient(config()) as client:
            page_reader = PageReader[PageBackendType, BackendType]()
            backend_types_api = BackendTypesApi(client)
            backend_types: List[BackendType] = await page_reader.get_all(
                backend_types_api.read_backend_types_backend_types_get
            )
        return backend_types

    def _construct_backends(self) -> List[QIBackend]:
        """Construct QIBackend using fetched backendtypes and metadata."""
        qi_backend_types = run_async(self._fetch_qi_backend_types())
        qi_backends = [QIBackend(provider=self, backend_type=backend_type) for backend_type in qi_backend_types]
        return qi_backends

    def backends(self) -> Sequence[QIBackend]:
        return self._qiskit_backends

    def get_backend(self, name: Optional[str] = None, id: Optional[int] = None) -> QIBackend:
        filter_arguments: dict[str, Any] = {}

        if name is not None:
            filter_arguments["name"] = name

        if id is not None:
            filter_arguments["id"] = id

        for backend in self._qiskit_backends:
            if all(getattr(backend, key) == value for key, value in filter_arguments.items()):
                return backend

        raise ValueError(f"Backend {name} not found")
