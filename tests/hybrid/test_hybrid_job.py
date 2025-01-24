from unittest.mock import MagicMock

from qi2_shared.hybrid.quantum_interface import ExecuteCircuitResult
from qiskit import QuantumCircuit
from qiskit.result.models import ExperimentResultData

from qiskit_quantuminspire.hybrid.hybrid_backend import QIHybridBackend
from qiskit_quantuminspire.hybrid.hybrid_job import QIHybridJob


def test_submit(quantum_interface: MagicMock) -> None:
    backend = QIHybridBackend(quantum_interface)
    circuit = QuantumCircuit(2, 2)
    quantum_interface.execute_circuit.return_value = ExecuteCircuitResult(
        shots_requested=2024,
        shots_done=1024,
        results={
            "00": 256,
            "01": 256,
            "10": 256,
            "11": 256,
        },
        raw_data=None,
    )
    job = QIHybridJob(run_input=[circuit], backend=backend, quantum_interface=quantum_interface)
    job.submit()

    actual_result = job.result()
    expected_result_data = ExperimentResultData(counts={"0x0": 256, "0x1": 256, "0x2": 256, "0x3": 256})

    assert actual_result.data(circuit) == expected_result_data.to_dict()


# TODO: test raw data
