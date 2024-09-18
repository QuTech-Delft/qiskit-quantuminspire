from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockFixture

from qiskit_quantuminspire.api.pagination import PageReader


@pytest.fixture
def page_reader_mock(mocker: MockFixture) -> AsyncMock:
    # Simply calling mocker.patch() doesn't work because PageReader is a generic class
    page_reader_mock = AsyncMock()
    page_reader_mock.get_all = AsyncMock()
    mocker.patch.object(PageReader, "get_all", page_reader_mock.get_all)
    return page_reader_mock
