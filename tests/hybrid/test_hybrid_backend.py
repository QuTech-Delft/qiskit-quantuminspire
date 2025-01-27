from typing import Generator
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from qi2_shared.hybrid.quantum_interface import ExecuteCircuitResult
from qiskit import QuantumCircuit
from qiskit.providers.models.backendstatus import BackendStatus
from qiskit.result.models import ExperimentResultData

from qiskit_quantuminspire import cqasm
from qiskit_quantuminspire.hybrid.hybrid_backend import QIHybridBackend


@pytest.fixture()
def qi_hybrid_job_mock(mocker: MockerFixture) -> Generator[MagicMock, None, None]:
    job = MagicMock()
    job.submit = MagicMock()
    mocker.patch("qiskit_quantuminspire.hybrid.hybrid_backend.QIHybridJob", return_value=job)
    yield job
    job.submit.reset_mock()


def test_status(quantum_interface: MagicMock) -> None:
    backend = QIHybridBackend(quantum_interface)
    # Exact BackendStatus is not important
    assert type(backend.status) is BackendStatus


def test_submit(quantum_interface: MagicMock, qi_hybrid_job_mock: MagicMock) -> None:
    backend = QIHybridBackend(quantum_interface)
    backend.run([])
    qi_hybrid_job_mock.submit.assert_called_once()


def test_raw_data(quantum_interface: MagicMock) -> None:
    # Arrange
    backend = QIHybridBackend(quantum_interface)
    circuit = QuantumCircuit(2, 2)
    quantum_interface.execute_circuit.return_value = ExecuteCircuitResult(
        shots_requested=5,
        shots_done=4,
        results={
            "00": 1,
            "01": 1,
            "10": 2,
        },
        raw_data=["00", "10", "10", "01"],
    )

    # Act
    results = backend.run(circuit, shots=5, memory=True).result()

    # Assert
    quantum_interface.execute_circuit.assert_called_once_with(cqasm.dumps(circuit), 5, raw_data_enabled=True)
    experiment_data = ExperimentResultData(counts={"0x0": 1, "0x1": 1, "0x2": 2}, memory=["0x0", "0x2", "0x2", "0x1"])

    assert results.data(circuit) == experiment_data.to_dict()
