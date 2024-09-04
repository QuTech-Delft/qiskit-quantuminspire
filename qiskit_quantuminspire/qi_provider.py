import asyncio
from datetime import datetime, timezone
from typing import Any, List, Union

from compute_api_client import ApiClient, BackendType, BackendTypesApi, Metadata

from qiskit_quantuminspire.api.client import config
from qiskit_quantuminspire.qi_backend import QIBackend


class QIProvider:
    """List QIBackends integrated with QiskitBackend interface."""

    def __init__(self) -> None:
        self._qiskit_backends = self._construct_backends()

    def _fetch_qi_backend_metadata(self, backend_type: BackendType) -> Metadata:
        """Fetch backend metadata using api client."""
        return Metadata(id=1, backend_id=1, created_on=datetime.now(timezone.utc), data={"nqubits": 6})

    async def _fetch_qi_backend_types(self) -> List[BackendType]:
        """Fetch backend types from CJM using api client."""
        async with ApiClient(config()) as client:
            backend_types_api = BackendTypesApi(client)
            backend_type_list = await backend_types_api.read_backend_types_backend_types_get()
        return backend_type_list.items

    def _construct_backends(self) -> List[QIBackend]:
        """Construct QIBackend using fetched backendtypes and metadata."""
        qi_backend_types = asyncio.run(self._fetch_qi_backend_types())
        qi_backends = [
            QIBackend(provider=self, backend_type=backend_type, metadata=self._fetch_qi_backend_metadata(backend_type))
            for backend_type in qi_backend_types
        ]
        return qi_backends

    def backends(self, name: Union[str, None] = None, **kwargs: Any) -> List[QIBackend]:
        return self._qiskit_backends

    def get_backend(self, name: Union[str, None] = None, **kwargs: Any) -> QIBackend:
        return self._qiskit_backends[0]
