from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockFixture

from qiskit_quantuminspire.qi_backend import QIBackend
from qiskit_quantuminspire.qi_provider import QIProvider
from tests.helpers import create_backend_type


@pytest.fixture
def mock_api(mocker: MockFixture) -> None:
    mocker.patch("qiskit_quantuminspire.qi_provider.ApiClient")
    mocker.patch("qiskit_quantuminspire.qi_provider.config")
    mocker.patch("qiskit_quantuminspire.qi_provider.BackendTypesApi")


def test_qi_provider_construct(mock_api: Any, page_reader_mock: AsyncMock) -> None:
    # Arrange
    page_reader_mock.get_all.return_value = [
        create_backend_type(name="qi_backend_1"),
        create_backend_type(name="spin"),
    ]

    # Act
    provider = QIProvider()

    # Assert
    assert len(provider.backends()) == 2
    assert all([isinstance(backend, QIBackend) for backend in provider.backends()])
