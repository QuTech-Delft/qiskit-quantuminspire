from pprint import PrettyPrinter
from typing import Any, List, Union

from compute_api_client import ApiClient, BackendStatus, BackendType, BackendTypesApi
from qi2_shared.client import config
from qi2_shared.utils import run_async
from qiskit.circuit import QuantumCircuit
from qiskit.providers import BackendV2 as Backend
from qiskit.providers.options import Options
from qiskit.transpiler import CouplingMap, Target

from qiskit_quantuminspire.mapping.instruction_mapping import InstructionMapping
from qiskit_quantuminspire.qi_jobs import QIJob
from qiskit_quantuminspire.utils import is_coupling_map_complete

_IGNORED_GATES: set[str] = {
    # Prep not viewed as separate gates in Qiskit
    "prep_x",
    "prep_y",
    "prep_z",
    # Measure x and y not natively supported https://github.com/Qiskit/qiskit/issues/3967
    "measure_x",
    "measure_y",
    "measure_all",
    # Measure z is equivalent to measure
    "measure_z",
    # May be supportable through parameterized CPhaseGate.
    # For now, direct usage of CPhaseGate is required
    "crk",
    # No direct qiskit equivalent
    "x90",
    "mx90",
    "y90",
    "my90",
    # Qiskit assumes barrier support and does not include it in its standard gate mapping
    "barrier",
}


# Ignore type checking for QIBackend due to missing Qiskit type stubs,
# which causes the base class 'Backend' to be treated as 'Any'.
class QIBaseBackend(Backend):  # type: ignore[misc]
    _max_shots: int

    def __init__(self, backend_type: BackendType, mapping: InstructionMapping = InstructionMapping(), **kwargs: Any):
        super().__init__(name=backend_type.name, description=backend_type.description, **kwargs)
        self._id: int = backend_type.id

        self._max_shots: int = backend_type.max_number_of_shots

        # Construct options
        self._options = self._default_options()
        self.set_options(shots=backend_type.default_number_of_shots)

        if not backend_type.supports_raw_data:
            self._options.set_validator("memory", [False])

        # Determine supported gates
        opensquirrel_gates = {inst.lower() for inst in mapping.supported_opensquirrel_instructions()}
        available_gates = opensquirrel_gates - _IGNORED_GATES

        # Construct coupling map
        coupling_map = CouplingMap(backend_type.topology)
        coupling_map_complete = is_coupling_map_complete(coupling_map)

        if "toffoli" in available_gates and not coupling_map_complete:
            # "Toffoli gate not supported for non-complete topology
            available_gates.remove("toffoli")

        self._target = Target().from_configuration(
            basis_gates=[mapping.opensquirrel_to_qiskit(gate) for gate in available_gates],
            num_qubits=backend_type.nqubits,
            coupling_map=None if coupling_map_complete else coupling_map,
        )

    def __repr_pretty__(self, p: PrettyPrinter) -> None:
        p.pprint(f"QIBackend(name={self.name}, id={self.id})")

    def __repr__(self) -> str:
        module_name = self.__class__.__module__
        s = f"<{module_name}.{self.__class__.__name__} object at 0x{id(self):x} (name={self.name}, id={self.id})>"
        return s

    @classmethod
    def _default_options(cls) -> Options:
        """Only options defined here are supported by the backend.

        shots: int: Number of shots for the job.
        """
        options = Options(shots=1024, seed_simulator=None, memory=False)

        # Seed_simulator is included in options to enable use of BackendEstimatorV2 in Qiskit,
        # but is not actually supported by the backend so any other value than none raises an error.
        options.set_validator("seed_simulator", [None])

        options.set_validator("shots", int)
        options.set_validator("memory", bool)

        return options

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


class QIBackend(QIBaseBackend):
    """A wrapper class for QuantumInspire backendtypes to integrate with Qiskit's Backend interface."""

    @property
    def status(self) -> BackendStatus:
        backend_type: BackendType = run_async(self._get_backend_type())
        return backend_type.status

    async def _get_backend_type(self) -> BackendType:
        async with ApiClient(config()) as client:
            backend_types_api = BackendTypesApi(client)
            return await backend_types_api.read_backend_type_backend_types_id_get(self._id)

    @property
    def available(self) -> bool:
        return bool(self.status != BackendStatus.OFFLINE)

    def run(self, run_input: Union[QuantumCircuit, List[QuantumCircuit]], **options: Any) -> QIJob:
        """Create and run a (batch)job on an QuantumInspire Backend.

        Args:
            run_input: A single or list of Qiskit QuantumCircuit objects or hybrid algorithms.

        Returns:
            QIJob: A reference to the batch job that was submitted.
        """
        if not self.available:
            raise RuntimeError(f"{self.name} is {self.status.value}, jobs can't be submitted")
        self.set_options(**options)
        job = QIJob(run_input=run_input, backend=self)
        job.submit()
        return job
