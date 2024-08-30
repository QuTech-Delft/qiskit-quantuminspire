from qiskit.providers import BackendV2 as Backend
from qiskit.providers.options import Options
from qiskit.transpiler import Target
from typing import Union

from qiskit_quantuminspire.qi_jobs import QIJob
from compute_api_client import BackendType, Metadata


class QIBackend(Backend):
    """A wrapper class for QuantumInspire backendtypes to integrate with Qiskit's Backend interface."""

    def __init__(self, backend_type: BackendType, metadata: Metadata, *args, **kwargs):
        super().__init__(name=backend_type.name, description=backend_type.description, *args, **kwargs)
        self._target = Target(num_qubits=metadata.data["nqubits"])

    @classmethod
    def _default_options(cls) -> Options:
        return Options(shots=1024, optimization_level=1)

    def target(self) -> Target:
        return self._target

    @property
    def max_circuits(self) -> Union[int, None]:
        return None

    def run(self, run_input, **options) -> QIJob:
        """Create and run a (batch)job on an QuantumInspire Backend.

        Args:
            run_input: A single or list of Qiskit QuantumCircuit objects or hybrid algorithms.

        Returns:
            QIJob: A reference to the batch job that was submitted.
        """
        job = QIJob(run_input=run_input, backend=self, job_id=None)
        job.submit()
        return job
