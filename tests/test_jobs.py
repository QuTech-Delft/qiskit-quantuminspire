import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from qiskit.providers.jobstatus import JobStatus

from qiskit_quantuminspire.qi_jobs import QIJob


def test_result(mocker: MockerFixture) -> None:
    job = QIJob(run_input="", backend=None, job_id="some-id")

    mocker.patch.object(job, "status", return_value=JobStatus.DONE)

    mock_fetch_job_results = AsyncMock(return_value=[MagicMock()])
    mocker.patch.object(job, "_fetch_job_results", mock_fetch_job_results)

    mock_process = mocker.patch(
        "qiskit_quantuminspire.qi_jobs.QIResult.process",
        return_value=MagicMock(),
    )

    job.result()

    assert mock_fetch_job_results.called
    mock_process.assert_called_once()


def test_result_raises_error_when_status_not_done(mocker: MockerFixture) -> None:
    job = QIJob(run_input="", backend=None, job_id="some-id")

    mocker.patch.object(job, "status", return_value=JobStatus.RUNNING)

    with pytest.raises(RuntimeError):
        job.result()


def test_fetch_job_result(mocker: MockerFixture) -> None:

    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.config",
        return_value=MagicMock(),
    )
    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.ApiClient",
        autospec=True,
    )
    n_jobs = 3

    mock_results_api = MagicMock()
    mock_get_result_by_id = AsyncMock()
    mock_get_result_by_id.side_effect = [MagicMock() for _ in range(n_jobs)]
    mock_results_api.read_results_by_job_id_results_job_job_id_get = mock_get_result_by_id

    mock_results_api = mocker.patch("qiskit_quantuminspire.qi_jobs.ResultsApi", return_value=mock_results_api)

    job = QIJob(run_input="", backend=None, job_id="some-id")

    job._job_ids = [str(i) for i in range(n_jobs)]

    results = asyncio.run(job._fetch_job_results())

    assert len(results) == n_jobs
    assert mock_get_result_by_id.call_count == n_jobs
