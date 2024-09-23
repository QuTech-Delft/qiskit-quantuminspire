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
    mocker: MockerFixture, mock_api_client: MagicMock, mock_job_api: MagicMock,
    mock_batchjob_api: MagicMock, backend: MagicMock
) -> None:

    qc = QuantumCircuit()
    job = QIJob(run_input=qc, backend=backend)
    mock_job_api.create_job_jobs_post.return_value = job

    await job.submit()

    assert mock_api_client.create_project_projects_post.call_args_list[2].id == 2
    assert mock_job_api.create_job_jobs_post.call_count == 1
    assert mock_batchjob_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1


@pytest.mark.asyncio
async def test_submit_multiple_jobs(
    mocker: MockerFixture, mock_job_api: MagicMock, mock_batchjob_api: MagicMock, backend: MagicMock
) -> None:

    run_input = [QuantumCircuit(), QuantumCircuit(), QuantumCircuit()]
    job = QIJob(run_input=run_input, backend=backend)
    mock_job_api.create_job_jobs_post.return_value = job

    await job.submit()

    assert mock_job_api.create_job_jobs_post.call_count == 3
    assert mock_batchjob_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1
