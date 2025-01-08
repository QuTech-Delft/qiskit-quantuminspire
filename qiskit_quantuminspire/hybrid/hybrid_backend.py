from typing import Any, List, Union

from qiskit import QuantumCircuit
from qiskit.providers.models.backendstatus import BackendStatus

from qiskit_quantuminspire.hybrid.hybrid_job import QIHybridJob
from qiskit_quantuminspire.hybrid.quantum_interface import QuantumInterface
from qiskit_quantuminspire.qi_backend import QIBaseBackend


class QIHybridBackend(QIBaseBackend):
    """Used as a Qiskit backend for hybrid algorithms that are fully executed on the Quantum Inspire platform.

    Quantum hardware specifications are inferred from the backend type selected on submission."""

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

    def run(self, run_input: Union[QuantumCircuit, List[QuantumCircuit]], **options: Any) -> QIHybridJob:
        job = QIHybridJob(run_input=run_input, backend=self, quantum_interface=self._quantum_interface, **options)
        job.submit()