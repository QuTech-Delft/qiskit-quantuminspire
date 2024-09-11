from unittest.mock import AsyncMock

import pytest
from compute_api_client import BackendType, PageBackendType

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
