from typing import Any, Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from qiskit.circuit import QuantumCircuit

from qiskit_quantuminspire.qi_jobs import QIJob


@pytest.fixture()
def api_mock(mocker: MockerFixture) -> Tuple[MagicMock, MagicMock]:

    config_mock = MagicMock()
    auth_settings = MagicMock()
    auth_settings.team_member_id = 1
    config_mock.auth_settings.return_value = auth_settings
    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.config",
        return_value=config_mock,
    )
    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.ApiClient",
        autospec=True,
    )

    project_api_mock = AsyncMock()
    project_mock = MagicMock()
    project_mock.id = 0
    project_api_mock.create_project_projects_post.return_value = project_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.ProjectsApi", return_value=project_api_mock)

    algorithms_api_mock = AsyncMock()
    algorithm_mock = MagicMock()
    algorithm_mock.id = 0
    algorithms_api_mock.create_algorithm_algorithms_post.return_value = algorithm_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.AlgorithmsApi", return_value=algorithms_api_mock)

    commits_api_mock = AsyncMock()
    commit_mock = MagicMock()
    commit_mock.id = 0
    commits_api_mock.create_commit_commits_post.return_value = commit_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.CommitsApi", return_value=commits_api_mock)

    files_api_mock = AsyncMock()
    file_mock = MagicMock()
    file_mock.id = 0
    files_api_mock.create_file_files_post.return_value = file_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.FilesApi", return_value=files_api_mock)

    batchjobs_api_mock = AsyncMock()
    batchjob_mock = MagicMock()
    batchjob_mock.id = 0
    batchjobs_api_mock.create_batch_job_batch_jobs_post.return_value = batchjob_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.BatchJobsApi", return_value=batchjobs_api_mock)

    jobs_api_mock = AsyncMock()
    job_mock = MagicMock()
    job_mock.id = 0
    jobs_api_mock.create_job_jobs_post.return_value = job_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.JobsApi", return_value=jobs_api_mock)

    return (jobs_api_mock, batchjobs_api_mock)


@pytest.fixture()
def backend(mocker: MockerFixture) -> MagicMock:
    backend_mock = MagicMock()
    backend_mock.options = MagicMock()

    def get_mock(var: str, default: Any = None) -> Any:
        options = {"number_of_shots": 1000}
        return options.get(var)

    backend_mock.options.get = get_mock
    backend_mock.id = 0
    return backend_mock


@pytest.mark.asyncio
async def test_submit_single_job(
    mocker: MockerFixture, api_mock: Tuple[MagicMock, MagicMock], backend: MagicMock
) -> None:

    mock_jobs_api, mock_batchjobs_api = api_mock

    qc = QuantumCircuit()
    job = QIJob(run_input=qc, backend=backend)
    mock_jobs_api.create_job_jobs_post.return_value = job

    await job.submit()

    assert mock_jobs_api.create_job_jobs_post.call_count == 1
    assert mock_batchjobs_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1


@pytest.mark.asyncio
async def test_submit_multiple_jobs(
    mocker: MockerFixture, api_mock: Tuple[MagicMock, MagicMock], backend: MagicMock
) -> None:

    mock_jobs_api, mock_batchjobs_api = api_mock

    run_input = [QuantumCircuit(), QuantumCircuit(), QuantumCircuit()]
    job = QIJob(run_input=run_input, backend=backend)
    mock_jobs_api.create_job_jobs_post.return_value = job

    await job.submit()

    assert mock_jobs_api.create_job_jobs_post.call_count == 3
    assert mock_batchjobs_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1
