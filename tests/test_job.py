from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from qiskit.circuit import QuantumCircuit

from qiskit_quantuminspire.qi_jobs import QIJob


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
    mocker: MockerFixture,
    mock_api_client: MagicMock,
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
    mock_job_api.create_job_jobs_post.return_value = job

    await job.submit()

    assert mock_project_api.create_project_projects_post.call_args_list[0][0][0].owner_id == 1
    assert mock_algorithms_api.create_algorithm_algorithms_post.call_args_list[0][0][0].project_id == 1
    assert mock_commits_api.create_commit_commits_post.call_args_list[0][0][0].algorithm_id == 1
    assert mock_files_api.create_file_files_post.call_args_list[0][0][0].commit_id == 1
    assert mock_job_api.create_job_jobs_post.call_args_list[0][0][0].file_id == 1
    assert mock_job_api.create_job_jobs_post.call_count == 1
    assert mock_batchjob_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1


@pytest.mark.asyncio
async def test_submit_multiple_jobs(
    mocker: MockerFixture,
    mock_api_client: MagicMock,
    mock_job_api: MagicMock,
    mock_batchjob_api: MagicMock,
    backend: MagicMock,
) -> None:

    run_input = [QuantumCircuit(), QuantumCircuit(), QuantumCircuit()]
    job = QIJob(run_input=run_input, backend=backend)
    mock_job_api.create_job_jobs_post.return_value = job

    await job.submit()

    assert mock_job_api.create_job_jobs_post.call_count == 3
    assert mock_batchjob_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1
