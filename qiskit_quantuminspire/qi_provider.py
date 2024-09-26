import asyncio
from typing import List, Union

from compute_api_client import ApiClient, BackendType, BackendTypesApi, PageBackendType

from qiskit_quantuminspire.api.client import config
from qiskit_quantuminspire.api.pagination import PageReader
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
        qi_backend_types = asyncio.run(self._fetch_qi_backend_types())
        qi_backends = [QIBackend(provider=self, backend_type=backend_type) for backend_type in qi_backend_types]
        return qi_backends

    def backends(self) -> List[QIBackend]:
        return self._qiskit_backends

    def get_backend(self, name: Union[str, None] = None) -> QIBackend:
        if name is None:
            return self._qiskit_backends[0]

        for backend in self._qiskit_backends:
            if backend.name == name:
                return backend
        raise ValueError(f"Backend {name} not found")
