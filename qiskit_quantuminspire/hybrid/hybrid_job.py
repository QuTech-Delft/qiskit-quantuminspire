from datetime import datetime
from functools import cache
from typing import Any, List, Union, cast

from compute_api_client import Result as RawJobResult
from qi2_shared.hybrid.quantum_interface import QuantumInterface
from qiskit import QuantumCircuit, transpile
from qiskit.providers.backend import BackendV2
from qiskit.providers.jobstatus import JobStatus
from qiskit.result.result import Result

from qiskit_quantuminspire import cqasm
from qiskit_quantuminspire.qi_jobs import QIBaseJob


class QIHybridJob(QIBaseJob):
    """Used internally as a Qiskit job for hybrid algorithms that are fully executed on the Quantum Inspire platform.

    Not to be used in user code.
    """

    def __init__(
        self,
        run_input: Union[QuantumCircuit, List[QuantumCircuit]],
        backend: Union[BackendV2, None],
        quantum_interface: QuantumInterface,
        **kwargs: Any,
    ) -> None:
        self._quantum_interface = quantum_interface
        super().__init__(run_input, backend, **kwargs)

    def status(self) -> JobStatus:
        """Quantum jobs in a hybrid environment are executed synchronously."""
        return JobStatus.DONE

    def submit(self) -> None:
        options = cast(dict[str, Any], self.backend().options)

        for circuit_data in self.circuits_run_data:
            transpiled_circuit = transpile(circuit_data.circuit, backend=self.backend())
            result = self._quantum_interface.execute_circuit(
                cqasm.dumps(transpiled_circuit), options.get("shots"), raw_data_enabled=options.get("memory")
            )

            # Store retrieved results in format expected by Job
            circuit_data.results = RawJobResult(
                id=0,
                created_on=datetime.now(),
                job_id=0,
                metadata_id=0,
                execution_time_in_seconds=0,
                shots_requested=result.shots_requested,
                shots_done=result.shots_done,
                results=result.results,
                raw_data=result.raw_data,
            )

    @cache
    def result(self) -> Result:
        return self._process_results()
