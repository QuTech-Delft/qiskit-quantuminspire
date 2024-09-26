import logging
import math
from typing import Any, List, Union

from compute_api_client import BackendType
from qiskit.circuit import Instruction, Measure, QuantumCircuit
from qiskit.circuit.library import (
    CCXGate,
    CPhaseGate,
    CXGate,
    IGate,
    RXGate,
    RYGate,
    SdgGate,
    TdgGate,
    get_standard_gate_name_mapping,
)
from qiskit.circuit.parameter import Parameter
from qiskit.providers import BackendV2 as Backend
from qiskit.providers.options import Options
from qiskit.transpiler import CouplingMap, Target

from qiskit_quantuminspire.qi_jobs import QIJob
from qiskit_quantuminspire.utils import is_coupling_map_complete

# Used for parameterizing Qiskit gates in the gate mapping
_THETA = Parameter("ϴ")

# Custom gate mapping for gates whose name do not match between cQASM and Qiskit
_CQASM_QISKIT_GATE_MAPPING: dict[str, Instruction] = {
    "i": IGate(),
    "x90": RXGate(math.pi / 2),
    "mx90": RXGate(-math.pi / 2),
    "y90": RYGate(math.pi / 2),
    "my90": RYGate(-math.pi / 2),
    "toffoli": CCXGate(),
    "sdag": SdgGate(),
    "tdag": TdgGate(),
    "cr": CPhaseGate(_THETA),
    "cnot": CXGate(),
    "measure_z": Measure(),
}

_IGNORED_GATES: list[str] = [
    # Prep not viewed as separate gates in Qiskit
    "prep_x",
    "prep_y",
    "prep_z",
    # Measure x and y not natively supported https://github.com/Qiskit/qiskit/issues/3967
    "measure_x",
    "measure_y",
    "measure_all",
    # May be supportable through parameterized CPhaseGate.
    # For now, direct usage of CPhaseGate is required
    "crk",
]

_ALL_SUPPORTED_GATES: list[str] = list(get_standard_gate_name_mapping().keys()) + list(
    _CQASM_QISKIT_GATE_MAPPING.keys()
)


# Ignore type checking for QIBackend due to missing Qiskit type stubs,
# which causes the base class 'Backend' to be treated as 'Any'.
class QIBackend(Backend):  # type: ignore[misc]
    """A wrapper class for QuantumInspire backendtypes to integrate with Qiskit's Backend interface."""

    _max_shots: int

    def __init__(self, backend_type: BackendType, **kwargs: Any):
        super().__init__(name=backend_type.name, description=backend_type.description, **kwargs)
        self._id: int = backend_type.id

        self._max_shots: int = backend_type.max_number_of_shots
        self._default_shots: int = backend_type.default_number_of_shots

        native_gates = [gate.lower() for gate in backend_type.gateset]
        available_gates = [gate for gate in native_gates if gate in _ALL_SUPPORTED_GATES]
        unknown_gates = set(native_gates) - set(_ALL_SUPPORTED_GATES) - set(_IGNORED_GATES)
        coupling_map = CouplingMap(backend_type.topology)
        coupling_map_complete = is_coupling_map_complete(coupling_map)

        if len(unknown_gates) > 0:
            logging.warning(f"Ignoring unknown native gate(s) {unknown_gates} for backend {backend_type.name}")

        if "toffoli" in available_gates and not coupling_map_complete:
            available_gates.remove("toffoli")
            logging.warning(
                f"Native toffoli gate in backend {backend_type.name} not supported for non-complete topology"
            )

        self._target = Target().from_configuration(
            basis_gates=available_gates,
            num_qubits=backend_type.nqubits,
            coupling_map=None if coupling_map_complete else coupling_map,
            custom_name_mapping=_CQASM_QISKIT_GATE_MAPPING,
        )

    @classmethod
    def _default_options(cls) -> Options:
        return Options(shots=1024, optimization_level=1)

    @property
    def target(self) -> Target:
        return self._target

    @property
    def max_shots(self) -> int:
        return self._max_shots

    @property
    def max_circuits(self) -> Union[int, None]:
        return None

    @property
    def id(self) -> int:
        return self._id

    @property
    def default_shots(self) -> int:
        return self._default_shots

    def run(self, run_input: Union[QuantumCircuit, List[QuantumCircuit]], **options: Any) -> QIJob:
        """Create and run a (batch)job on an QuantumInspire Backend.

        Args:
            run_input: A single or list of Qiskit QuantumCircuit objects or hybrid algorithms.

        Returns:
            QIJob: A reference to the batch job that was submitted.
        """
        job = QIJob(run_input=run_input, backend=self)
        job.submit()
        return job
