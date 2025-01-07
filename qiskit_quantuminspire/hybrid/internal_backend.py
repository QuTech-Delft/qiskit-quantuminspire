from typing import Any, List, Union

from qi2_shared.hybrid.quantum_interface import QuantumInterface
from qiskit import QuantumCircuit
from qiskit.providers.models.backendstatus import BackendStatus

from qiskit_quantuminspire.hybrid.internal_job import QIInternalJob
from qiskit_quantuminspire.qi_backend import QIBaseBackend


class QIInternalBackend(QIBaseBackend):
    def __init__(self, qi: QuantumInterface, **kwargs: Any):
        super().__init__(qi.backend_type, **kwargs)
        self._quantum_interface = qi

    @property
    def status(self) -> BackendStatus:
        """Return the backend status. Pending jobs is always 0. This information is currently not known.

        Returns:
            BackendStatus: the status of the backend. Pending jobs is always 0.
        """
        return BackendStatus(
            backend_name=self._quantum_interface.backend_type.name,
            backend_version="2.0",
            operational=True,
            pending_jobs=0,
            status_msg="online",
        )

    def run(self, run_input: Union[QuantumCircuit, List[QuantumCircuit]], **options: Any) -> QIInternalJob:
        raise NotImplementedError()
