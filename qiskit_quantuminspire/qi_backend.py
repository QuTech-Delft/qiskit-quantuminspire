import math
from typing import Any, List, Union

from compute_api_client import BackendType
from qiskit.circuit import Gate, QuantumCircuit
from qiskit.circuit.library import IGate, RXGate, RYGate, get_standard_gate_name_mapping
from qiskit.providers import BackendV2 as Backend
from qiskit.providers.options import Options
from qiskit.transpiler import CouplingMap, Target

from qiskit_quantuminspire.qi_jobs import QIJob


# Ignore type checking for QIBackend due to missing Qiskit type stubs,
# which causes the base class 'Backend' to be treated as 'Any'.
class QIBackend(Backend):  # type: ignore[misc]
    """A wrapper class for QuantumInspire backendtypes to integrate with Qiskit's Backend interface."""

    _max_shots: int

    _CQASM_QISKIT_GATE_MAPPING: dict[str, Gate] = {
        "i": IGate(),
        "x90": RXGate(math.pi / 2),
        "mx90": RXGate(-math.pi / 2),
        "y90": RYGate(math.pi / 2),
        "my90": RYGate(-math.pi / 2),
    }

    def __init__(self, backend_type: BackendType, **kwargs: Any):
        super().__init__(name=backend_type.name, description=backend_type.description, **kwargs)
        self._max_shots = backend_type.max_number_of_shots
        all_supported_gates: list[str] = list(get_standard_gate_name_mapping().keys()) + list(
            self._CQASM_QISKIT_GATE_MAPPING.keys()
        )
        available_gates = [gate.lower() for gate in backend_type.gateset if gate.lower() in all_supported_gates]
        self._target = Target().from_configuration(
            basis_gates=available_gates,
            num_qubits=backend_type.nqubits,
            coupling_map=CouplingMap(backend_type.topology),
            custom_name_mapping=self._CQASM_QISKIT_GATE_MAPPING,
        )

    @classmethod
    def _default_options(cls) -> Options:
        return Options(shots=1024, optimization_level=1)

    def target(self) -> Target:
        return self._target

    @property
    def max_shots(self) -> int:
        return self._max_shots

    @property
    def max_circuits(self) -> Union[int, None]:
        return None

    def run(self, run_input: Union[QuantumCircuit, List[QuantumCircuit]], **options: Any) -> QIJob:
        """Create and run a (batch)job on an QuantumInspire Backend.

        Args:
            run_input: A single or list of Qiskit QuantumCircuit objects or hybrid algorithms.

        Returns:
            QIJob: A reference to the batch job that was submitted.
        """
        job = QIJob(run_input=run_input, backend=self, job_id="some-random-id")
        job.submit()
        return job
