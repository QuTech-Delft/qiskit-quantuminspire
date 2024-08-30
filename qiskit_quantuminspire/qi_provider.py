from datetime import datetime, timezone
from typing import Any, List, Union

from compute_api_client import BackendStatus, BackendType, Metadata

from qiskit_quantuminspire.qi_backend import QIBackend


class QIProvider:
    """List QIBackends integrated with QiskitBackend interface."""

    def __init__(self) -> None:
        self._qiskit_backends = self._construct_backends()

    def _fetch_qi_backend_metadata(self) -> List[Metadata]:
        """Fetch backend metadata using api client."""
        return [Metadata(id=1, backend_id=1, created_on=datetime.now(timezone.utc), data={"nqubits": 6})]

    def _fetch_qi_backend_types(self) -> List[BackendType]:
        """Fetch backend types from CJM using api client."""
        backend_type_list = [
            BackendType(
                id=2,
                name="Spin 2",
                infrastructure="Hetzner",
                description="Silicon spin quantum computer",
                image_id="abcd1234",
                is_hardware=True,
                features=["multiple_measurements"],
                default_compiler_config={},
                native_gateset={"single_qubit_gates": ["X"]},
                status=BackendStatus.IDLE,
                default_number_of_shots=1024,
                max_number_of_shots=2048,
            ),
        ]
        return backend_type_list

    def _construct_backends(self) -> List[QIBackend]:
        """Construct QIBackend using fetched backendtypes and metadata."""
        qi_backend_types = self._fetch_qi_backend_types()
        qi_metadata = self._fetch_qi_backend_metadata()
        qi_backends = [
            QIBackend(provider=self, backend_type=backend_type, metadata=metadata)
            for backend_type, metadata in zip(qi_backend_types, qi_metadata)
        ]
        return qi_backends

    def backends(self, name: Union[str, None] = None, **kwargs: Any) -> List[QIBackend]:
        return self._construct_backends()

    def get_backend(self, name: Union[str, None] = None, **kwargs: Any) -> QIBackend:
        return self._construct_backends()[0]
