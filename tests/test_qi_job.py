import asyncio
import tempfile
from typing import Any, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock

import pytest
from compute_api_client import JobStatus as QIJobStatus
from pytest_mock import MockerFixture
from qiskit import QuantumCircuit, qpy
from qiskit.providers import BackendV2
from qiskit.providers.exceptions import JobTimeoutError
from qiskit.providers.jobstatus import JobStatus
from qiskit.qobj import QobjExperimentHeader
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.result.result import Result

from qiskit_quantuminspire.base_provider import BaseProvider
from qiskit_quantuminspire.qi_backend import QIBackend
from qiskit_quantuminspire.qi_jobs import ExperimentFailedWarning, QIJob
from tests.helpers import create_backend_type, create_raw_job_result


class SingleBackendProvider(BaseProvider):
    """Returns only the provided backend and raises error on fetching backend with wrong name."""

    def __init__(self, backend: QIBackend) -> None:
        self.backend = backend

    def get_backend(self, name: Optional[str] = None, id: Optional[int] = None) -> QIBackend:
        if name:
            assert name == self.backend.name

        if id:
            assert id == self.backend.id

        return self.backend

    def backends(self) -> List[BackendV2]:
        return [self.backend]


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


@pytest.fixture()
def backend(mocker: MockerFixture) -> MagicMock:
    backend_mock = MagicMock()
    backend_mock.options = MagicMock()

    def get_mock(var: str, default: Any = None) -> Any:
        options = {"number_of_shots": 1000}
        return options.get(var)

    backend_mock.options.get = get_mock
    backend_mock.id = 0
    backend_mock.name = "qi_backend_1"
    return backend_mock


def test_result_blocking(mocker: MockerFixture) -> None:
    qc = QuantumCircuit(2, 2)

    job = QIJob(run_input=qc, backend=None)

    mock_wait_for_final_state = mocker.patch.object(job, "wait_for_final_state", return_value=None)
    mock_fetch_job_results = mocker.patch.object(
        job, "_fetch_job_results", return_value=AsyncMock(return_value=MagicMock())
    )
    mock_process_results = mocker.patch.object(job, "_process_results", return_value=MagicMock())

    for _ in range(4):  # Check caching
        job.result(wait_for_results=True)

    mock_wait_for_final_state.assert_called_once()
    mock_process_results.assert_called_once()
    mock_fetch_job_results.assert_called_once()


def test_result_blocking_timeout(mocker: MockerFixture) -> None:
    qc = QuantumCircuit(2, 2)

    job = QIJob(run_input=qc, backend=None)

    mocker.patch.object(job, "status", return_value="Random Status")

    with pytest.raises(JobTimeoutError):
        job.result(timeout=0.00001)


def test_result_non_blocking(mocker: MockerFixture, mock_api_client: MagicMock, mock_batchjob_api: MagicMock) -> None:
    job = QIJob(run_input="", backend=None)
    mocker.patch.object(job, "done", return_value=False)
    mock_wait_for_final_state = mocker.patch.object(job, "wait_for_final_state", return_value=None)
    with pytest.raises(RuntimeError):
        job.result(wait_for_results=False)
    mock_wait_for_final_state.assert_not_called()


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
    mocker: MockerFixture,
) -> None:
    circuits = [QuantumCircuit(1, 1), QuantumCircuit(2, 2)]

    page_reader_mock.get_all.side_effect = [[], [None]]

    job = QIJob(run_input=circuits, backend=None)

    job.circuits_run_data[0].job_id = 1
    job.circuits_run_data[1].job_id = 2

    mock_fetch_failed_jobs_message = mocker.patch.object(job, "_fetch_failed_jobs_message", return_value=AsyncMock())

    asyncio.run(job._fetch_job_results())

    assert all(circuit_data.results is None for circuit_data in job.circuits_run_data)

    assert len(job.circuits_run_data) == len(circuits)
    mock_fetch_failed_jobs_message.assert_awaited_once()


def test_fetch_failed_jobs_message(
    mocker: MockerFixture,
) -> None:
    class MockJob:
        def __init__(self, message: str, id: int, status: QIJobStatus):
            self.message = message
            self.id = id
            self.status = status

    # Arrange
    mock_jobs_api = MagicMock()
    job_ids_to_check = [1, 2]

    mock_jobs_api.read_job_jobs_id_get = AsyncMock(
        side_effect=[
            MockJob(id=job_ids_to_check[0], message="failed", status=QIJobStatus.FAILED),  # Failed job
            MockJob(id=job_ids_to_check[1], message="", status=QIJobStatus.COMPLETED),  # Job with no results
        ]
    )

    mocker.patch("qiskit_quantuminspire.qi_jobs.JobsApi", return_value=mock_jobs_api)

    circuits = [QuantumCircuit(1, 1), QuantumCircuit(2, 2)]

    job = QIJob(run_input=circuits, backend=None)
    job.circuits_run_data[0].job_id = job_ids_to_check[0]
    job.circuits_run_data[1].job_id = job_ids_to_check[1]

    # Act
    asyncio.run(job._fetch_failed_jobs_message(MagicMock(), job_ids_to_check))

    # Assert
    assert job.circuits_run_data[0].system_message == "failed"
    assert job.circuits_run_data[1].system_message == "No Results"


def test_process_results() -> None:
    backend_type = create_backend_type(name="qi_backend_1")
    qi_backend = QIBackend(backend_type=backend_type)
    qc = QuantumCircuit(2, 2)

    qi_job = QIJob(run_input=qc, backend=qi_backend)
    qi_job.batch_job_id = 100
    qi_job.circuits_run_data[0].job_id = 1
    qi_job.circuits_run_data[0].results = create_raw_job_result()

    processed_results = qi_job._process_results()
    experiment_data = ExperimentResultData(counts={"0x0": 256, "0x1": 256, "0x2": 256, "0x3": 256})
    experiment_result = ExperimentResult(
        shots=100,
        success=True,
        meas_level=2,
        data=experiment_data,
        header=QobjExperimentHeader(name=qi_job.circuits_run_data[0].circuit.name),
        status="Experiment successful",
    )
    expected_results = Result(
        backend_name="qi_backend_1",
        backend_version="1.0.0",
        qobj_id="",
        job_id="100",
        success=True,
        results=[experiment_result],
        date=None,
        status="Result successful",
        header=None,
        system_messages={},
    )
    assert processed_results.to_dict() == expected_results.to_dict()
    assert processed_results.data(qc) == experiment_data.to_dict()


def test_process_results_raw_data() -> None:
    backend_type = create_backend_type(name="qi_backend_1")
    qi_backend = QIBackend(backend_type=backend_type)
    qc = QuantumCircuit(2, 2)

    qi_job = QIJob(run_input=qc, backend=qi_backend)
    qi_job.batch_job_id = 100
    qi_job.circuits_run_data[0].job_id = 1
    qi_job.circuits_run_data[0].results = create_raw_job_result(
        results={
            "000": 2,
            "001": 1,
            "010": 2,
            "011": 3,
        },
        raw_data=["000", "001", "010", "011", "000", "010", "011", "011"],
    )

    processed_results = qi_job._process_results()
    experiment_data = ExperimentResultData(
        counts={"0x0": 2, "0x1": 1, "0x2": 2, "0x3": 3}, memory=["0x0", "0x1", "0x2", "0x3", "0x0", "0x2", "0x3", "0x3"]
    )

    assert processed_results.data(qc) == experiment_data.to_dict()


def test_process_results_handles_invalid_results() -> None:
    qi_backend = create_backend_type(name="qi_backend_1")
    qc = QuantumCircuit(2, 2)

    qi_job = QIJob(run_input=qc, backend=qi_backend)
    batch_job_id = 100
    qi_job.batch_job_id = batch_job_id
    qi_job.circuits_run_data[0].job_id = 1  # Individual job_id

    qi_job.circuits_run_data[0].results = None
    qi_job.circuits_run_data[0].system_message = "user-error, sytax error"

    with pytest.warns(ExperimentFailedWarning, match="Some experiments"):

        processed_results = qi_job._process_results()
        expected_results = Result(
            backend_name="qi_backend_1",
            backend_version="1.0.0",
            qobj_id="",
            job_id="100",
            success=False,
            results=[
                ExperimentResult(
                    shots=0,
                    success=False,
                    meas_level=2,
                    data=ExperimentResultData(counts={}),
                    header=QobjExperimentHeader(name=qi_job.circuits_run_data[0].circuit.name),
                    status="Experiment failed. System Message: user-error, sytax error",
                )
            ],
            date=None,
            status="Result failed",
            header=None,
            system_messages={qc.name: "user-error, sytax error"},
        )
        assert processed_results.to_dict() == expected_results.to_dict()


def test_submit_single_job(
    mocker: MockerFixture,
    mock_api_client: MagicMock,
    mock_language_api: MagicMock,
    mock_project_api: MagicMock,
    mock_algorithms_api: MagicMock,
    mock_commits_api: MagicMock,
    mock_files_api: MagicMock,
    mock_job_api: MagicMock,
    mock_batchjob_api: MagicMock,
    backend: MagicMock,
) -> None:
    qc = QuantumCircuit()
    job = QIJob(run_input=qc, backend=backend)

    job.submit()

    assert mock_project_api.create_project_projects_post.call_args_list[0][0][0].owner_id == 1
    assert mock_algorithms_api.create_algorithm_algorithms_post.call_args_list[0][0][0].project_id == 1
    assert mock_commits_api.create_commit_commits_post.call_args_list[0][0][0].algorithm_id == 1
    assert mock_files_api.create_file_files_post.call_args_list[0][0][0].commit_id == 1
    assert mock_job_api.create_job_jobs_post.call_args_list[0][0][0].file_id == 1
    assert mock_job_api.create_job_jobs_post.call_count == 1
    assert mock_batchjob_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1


def test_submit_multiple_jobs(
    mocker: MockerFixture,
    mock_api_client: MagicMock,
    mock_language_api: MagicMock,
    mock_project_api: MagicMock,
    mock_algorithms_api: MagicMock,
    mock_commits_api: MagicMock,
    mock_files_api: MagicMock,
    mock_batchjob_api: MagicMock,
    mock_job_api: MagicMock,
    backend: MagicMock,
) -> None:
    run_input = [QuantumCircuit(), QuantumCircuit(), QuantumCircuit()]
    job = QIJob(run_input=run_input, backend=backend)

    job.submit()

    assert mock_project_api.create_project_projects_post.call_args_list[0][0][0].owner_id == 1
    assert mock_batchjob_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1

    for n, _ in enumerate(run_input):
        assert mock_algorithms_api.create_algorithm_algorithms_post.call_args_list[n][0][0].project_id == 1
        assert mock_commits_api.create_commit_commits_post.call_args_list[n][0][0].algorithm_id == 1
        assert mock_files_api.create_file_files_post.call_args_list[n][0][0].commit_id == 1
        assert mock_job_api.create_job_jobs_post.call_args_list[n][0][0].file_id == 1

    assert mock_job_api.create_job_jobs_post.call_count == 3
    assert mock_batchjob_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1


def test_job_status(
    mocker: MockerFixture,
    mock_api_client: MagicMock,
    mock_language_api: MagicMock,
    mock_project_api: MagicMock,
    mock_algorithms_api: MagicMock,
    mock_commits_api: MagicMock,
    mock_files_api: MagicMock,
    mock_batchjob_api: MagicMock,
    mock_job_api: MagicMock,
    backend: MagicMock,
) -> None:
    qc = QuantumCircuit()
    job = QIJob(run_input=qc, backend=backend)

    status = job.status()

    assert status == JobStatus.QUEUED


def test_serialize_deserialize(backend: MagicMock) -> None:
    # Arrange
    qc1 = QuantumCircuit(3)
    qc2 = QuantumCircuit(3)

    qc2.h([0, 1])
    qc2.measure_all()

    qc1.x(0)
    qc1.y(1)
    qc1.z(2)
    qc1.measure_all()

    job = QIJob(run_input=[qc1, qc2], backend=backend)
    job.circuits_run_data[0].job_id = 1
    job.circuits_run_data[1].job_id = 2

    # Act
    with tempfile.TemporaryDirectory() as temp_dir:
        out_file = temp_dir + "/test.qpy"
        job.serialize(out_file)

        loaded_job = QIJob.deserialize(SingleBackendProvider(backend), out_file)

        # Assert
        assert loaded_job.circuits_run_data == job.circuits_run_data
        assert loaded_job.backend() == job.backend()


def test_deserialize_raises_error_on_missing_metadata(backend: MagicMock) -> None:
    # Arrange
    qc = QuantumCircuit(3)

    with tempfile.TemporaryDirectory() as temp_dir:
        out_file = temp_dir + "/test.qpy"

        # Dump with qpy so that metadata normally added by QIJob.serialize is missing
        with open(out_file, "wb") as f:
            qpy.dump([qc], f)

        # Act/Assert
        with pytest.raises(ValueError):
            QIJob.deserialize(SingleBackendProvider(backend), out_file)


def test_serialize_on_empty_job_raises_error(backend: MagicMock) -> None:
    # Arrange
    job = QIJob(run_input=[], backend=backend)

    # Act
    with tempfile.TemporaryDirectory() as temp_dir:
        out_file = temp_dir + "/test.qpy"

        # Act/Assert
        with pytest.raises(ValueError):
            job.serialize(out_file)
