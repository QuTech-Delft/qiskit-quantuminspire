import asyncio
from datetime import datetime, timezone
from typing import List, Union
from unittest.mock import AsyncMock, MagicMock

import pytest
from compute_api_client import Result as RawJobResult
from pytest_mock import MockerFixture
from qiskit import QuantumCircuit
from qiskit.qobj import QobjExperimentHeader
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.result.result import Result

from qiskit_quantuminspire.qi_jobs import QIJob
from tests.helpers import create_backend_type


@pytest.fixture
def mock_configs_apis(mocker: MockerFixture) -> None:
    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.config",
        return_value=MagicMock(),
    )
    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.ApiClient",
        autospec=True,
    )

    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.ResultsApi",
        autospec=True,
    )


def test_result(mocker: MockerFixture) -> None:

    qc = QuantumCircuit(2, 2)

    job = QIJob(run_input=qc, backend=None)

    mocker.patch.object(job, "done", return_value=True)

    mock_fetch_job_results = AsyncMock(return_value=MagicMock())
    mocker.patch.object(job, "_fetch_job_results", mock_fetch_job_results)

    mock_process_results = MagicMock(return_value=MagicMock())
    mocker.patch.object(job, "_process_results", mock_process_results)

    for _ in range(4):  # Check caching
        job.result()

    mock_process_results.assert_called_once()
    mock_fetch_job_results.assert_called_once()


def test_result_raises_error_when_status_not_done(mocker: MockerFixture) -> None:
    job = QIJob(run_input="", backend=None)
    mocker.patch.object(job, "done", return_value=False)
    with pytest.raises(RuntimeError):
        job.result()


@pytest.mark.parametrize(
    "circuits, expected_n_jobs",
    [
        (QuantumCircuit(1, 1), 1),  # Single circuit
        ([QuantumCircuit(1, 1), QuantumCircuit(2, 2)], 2),  # List of circuits
    ],
)
def test_fetch_job_result(
    page_reader_mock: AsyncMock,
    circuits: Union[QuantumCircuit, List[QuantumCircuit]],
    expected_n_jobs: int,
    mock_configs_apis: None,
) -> None:

    page_reader_mock.get_all.side_effect = [[MagicMock()] for _ in range(expected_n_jobs)]

    job = QIJob(run_input=circuits, backend=None)

    asyncio.run(job._fetch_job_results())

    assert len(job.circuits_run_data) == expected_n_jobs

    assert all(circuit_data.results for circuit_data in job.circuits_run_data)


def test_fetch_job_result_handles_invalid_results(
    page_reader_mock: AsyncMock,
    mock_configs_apis: None,
) -> None:

    circuits = [QuantumCircuit(1, 1), QuantumCircuit(2, 2)]

    page_reader_mock.get_all.side_effect = [[], [None]]

    job = QIJob(run_input=circuits, backend=None)

    asyncio.run(job._fetch_job_results())

    assert all(circuit_data.results is None for circuit_data in job.circuits_run_data)

    assert len(job.circuits_run_data) == len(circuits)


def test_process_results() -> None:
    qi_backend = create_backend_type(name="qi_backend_1")
    qc = QuantumCircuit(2, 2)

    qi_job = QIJob(run_input=qc, backend=qi_backend)
    batch_job_id = 100
    qi_job.batch_job_id = batch_job_id
    individual_job_id = 1
    qi_job.circuits_run_data[0].job_id = 1  #  Individual job_id
    qi_job.circuits_run_data[0].results = RawJobResult(
        id=individual_job_id,
        metadata_id=1,
        created_on=datetime(2022, 10, 25, 15, 37, 54, 269823, tzinfo=timezone.utc),
        execution_time_in_seconds=1.23,
        shots_requested=100,
        shots_done=100,
        results={
            "0000000000": 256,
            "0000000001": 256,
            "0000000010": 256,
            "0000000011": 256,
        },
        job_id=10,
    )
    processed_results = qi_job._process_results()
    experiment_data = ExperimentResultData(counts={"0x0": 256, "0x1": 256, "0x2": 256, "0x3": 256})
    experiment_result = ExperimentResult(
        shots=100,
        success=True,
        meas_level=2,
        data=experiment_data,
        header=QobjExperimentHeader(name=qi_job.circuits_run_data[0].circuit.name),
    )
    expected_results = Result(
        backend_name="qi_backend_1",
        backend_version="1.0.0",
        qobj_id="",
        job_id=batch_job_id,
        success=True,
        results=[experiment_result],
        date=None,
        status=None,
        header=None,
    )
    assert processed_results.to_dict() == expected_results.to_dict()
    assert processed_results.data(qc) == experiment_data.to_dict()


def test_process_results_handles_invalid_results() -> None:

    qi_backend = create_backend_type(name="qi_backend_1")
    qc = QuantumCircuit(2, 2)

    qi_job = QIJob(run_input=qc, backend=qi_backend)
    batch_job_id = 100
    qi_job.batch_job_id = batch_job_id
    qi_job.circuits_run_data[0].job_id = 1  # Individual job_id

    qi_job.circuits_run_data[0].results = None

    processed_results = qi_job._process_results()
    expected_results = Result(
        backend_name="qi_backend_1",
        backend_version="1.0.0",
        qobj_id="",
        job_id=batch_job_id,
        success=False,
        results=[
            ExperimentResult(
                shots=0,
                success=False,
                meas_level=2,
                data=ExperimentResultData(counts={}),
                header=QobjExperimentHeader(name=qi_job.circuits_run_data[0].circuit.name),
            )
        ],
        date=None,
        status=None,
        header=None,
    )
    assert processed_results.to_dict() == expected_results.to_dict()
