from unittest.mock import AsyncMock

import pytest
from compute_api_client import BackendType, BatchJob, PageBackendType, PageBatchJob
from pytest_mock import MockerFixture

from qiskit_quantuminspire.api.pagination import PageReader
from tests.helpers import create_backend_type


@pytest.mark.asyncio
async def test_pagination_get_all() -> None:
    # Arrange
    def returned_pages(page: int) -> PageBackendType:
        pages = [
            PageBackendType(
                items=[
                    create_backend_type(name="qi_backend_1"),
                    create_backend_type(name="spin"),
                ],
                total=5,
                page=1,
                size=2,
                pages=2,
            ),
            PageBackendType(
                items=[
                    create_backend_type(name="qi_backend2"),
                    create_backend_type(name="spin6"),
                    create_backend_type(name="spin7"),
                ],
                total=5,
                page=2,
                size=3,
                pages=2,
            ),
        ]
        return pages[page - 1]

    api_call = AsyncMock(side_effect=returned_pages)

    page_reader = PageReader[PageBackendType, BackendType]()

    # Act
    backends = await page_reader.get_all(api_call)

    # Assert
    actual_backend_names = [backend.name for backend in backends]
    expected_backend_names = ["qi_backend_1", "spin", "qi_backend2", "spin6", "spin7"]

    assert actual_backend_names == expected_backend_names


@pytest.mark.asyncio
async def test_pagination_get_single_error(mocker: MockerFixture) -> None:
    batchjob_patch = mocker.patch(
        "compute_api_client.BatchJob",
        autospec=True,
    )

    # Arrange
    def returned_jobs() -> PageBatchJob:
        pages = [
            PageBatchJob(
                items=[batchjob_patch, batchjob_patch, batchjob_patch],
                total=5,
                page=1,
                size=3,
                pages=2,
            )
        ]
        return pages[0]

    api_call = AsyncMock(side_effect=returned_jobs)

    page_reader = PageReader[PageBatchJob, BatchJob]()

    # Act
    with pytest.raises(RuntimeError):
        await page_reader.get_single(api_call)


@pytest.mark.asyncio
async def test_pagination_get_single(mocker: MockerFixture) -> None:
    batchjob_patch = mocker.patch(
        "compute_api_client.BatchJob",
        autospec=True,
    )

    # Arrange
    def returned_jobs() -> PageBatchJob:
        pages = [
            PageBatchJob(
                items=[batchjob_patch],
                total=1,
                page=1,
                size=1,
                pages=1,
            )
        ]
        return pages[0]

    api_call = AsyncMock(side_effect=returned_jobs)

    page_reader = PageReader[PageBatchJob, BatchJob]()

    # Act
    batchjob = await page_reader.get_single(api_call)

    assert batchjob == batchjob_patch
