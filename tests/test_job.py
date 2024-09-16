from unittest.mock import AsyncMock, MagicMock

from pytest_mock import MockerFixture

from qiskit_quantuminspire.qi_jobs import QIJob


async def test_submit_job(mocker: MockerFixture) -> None:

    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.config",
        return_value=MagicMock(),
    )
    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.ApiClient",
        autospec=True,
    )

    mocker.patch("qiskit_quantuminspire.qi_jobs.ProjectsApi", return_value=AsyncMock())
    mocker.patch("qiskit_quantuminspire.qi_jobs.AlgorithmsApi", return_value=AsyncMock())
    mocker.patch("qiskit_quantuminspire.qi_jobs.CommitsApi", return_value=AsyncMock())
    mocker.patch("qiskit_quantuminspire.qi_jobs.FilesApi", return_value=AsyncMock())
    mock_batchjobs_api = mocker.patch("qiskit_quantuminspire.qi_jobs.BatchJobsApi", return_value=AsyncMock())
    mock_jobs_api = mocker.patch("qiskit_quantuminspire.qi_jobs.JobsApi", return_value=AsyncMock())

    job = QIJob(run_input="", backend=None, job_id="some-id")
    mock_jobs_api.create_job_jobs_post.return_value = job
    mock_batchjobs_api.enqueue_batch_job_batch_jobs_id_enqueue_patch = AsyncMock()

    await job.submit()

    assert mock_batchjobs_api.enqueue_batch_job_batch_jobs_id_enqueue_patch.call_count == 1
