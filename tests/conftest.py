from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from qiskit_quantuminspire.api.pagination import PageReader


@pytest.fixture
def page_reader_mock(mocker: MockerFixture) -> AsyncMock:
    # Simply calling mocker.patch() doesn't work because PageReader is a generic class
    page_reader_mock = AsyncMock()
    page_reader_mock.get_all = AsyncMock()
    mocker.patch.object(PageReader, "get_all", page_reader_mock.get_all)
    return page_reader_mock


@pytest.fixture
def mock_api_client(mocker: MockerFixture) -> MagicMock:
    mocker.patch("qiskit_quantuminspire.qi_provider.BackendTypesApi")

    config_mock = MagicMock()
    auth_settings = MagicMock()
    auth_settings.team_member_id = 1
    config_mock.auth_settings.return_value = auth_settings
    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.config",
        return_value=config_mock,
    )

    return mocker.patch(
        "qiskit_quantuminspire.qi_jobs.ApiClient",
        autospec=True,
    )


@pytest.fixture
def mock_project_api(mocker: MockerFixture, mock_api_client: MagicMock) -> MagicMock:

    project_api_mock = AsyncMock()
    project_mock = MagicMock()
    project_mock.id = 1
    project_api_mock.create_project_projects_post.return_value = project_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.ProjectsApi", return_value=project_api_mock)
    return project_api_mock


@pytest.fixture
def mock_algorithms_api(mocker: MockerFixture, mock_project_api: MagicMock) -> MagicMock:
    algorithms_api_mock = AsyncMock()
    algorithm_mock = MagicMock()
    algorithm_mock.id = 1
    algorithms_api_mock.create_algorithm_algorithms_post.return_value = algorithm_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.AlgorithmsApi", return_value=algorithms_api_mock)
    return algorithms_api_mock


@pytest.fixture()
def mock_commits_api(mocker: MockerFixture, mock_algorithms_api: MagicMock) -> MagicMock:
    commits_api_mock = AsyncMock()
    commit_mock = MagicMock()
    commit_mock.id = 1
    commits_api_mock.create_commit_commits_post.return_value = commit_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.CommitsApi", return_value=commits_api_mock)
    return commits_api_mock


@pytest.fixture()
def mock_files_api(mocker: MockerFixture, mock_commits_api: MagicMock) -> MagicMock:
    files_api_mock = AsyncMock()
    file_mock = MagicMock()
    file_mock.id = 1
    files_api_mock.create_file_files_post.return_value = file_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.FilesApi", return_value=files_api_mock)
    return files_api_mock


@pytest.fixture()
def mock_job_api(mocker: MockerFixture, mock_files_api: MagicMock) -> MagicMock:
    jobs_api_mock = AsyncMock()
    job_mock = MagicMock()
    job_mock.id = 1
    jobs_api_mock.create_job_jobs_post.return_value = job_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.JobsApi", return_value=jobs_api_mock)
    return jobs_api_mock


@pytest.fixture()
def mock_batchjob_api(mocker: MockerFixture) -> MagicMock:
    batchjobs_api_mock = AsyncMock()
    batchjob_mock = MagicMock()
    batchjob_mock.id = 1
    batchjobs_api_mock.create_batch_job_batch_jobs_post.return_value = batchjob_mock
    mocker.patch("qiskit_quantuminspire.qi_jobs.BatchJobsApi", return_value=batchjobs_api_mock)
    return batchjobs_api_mock
