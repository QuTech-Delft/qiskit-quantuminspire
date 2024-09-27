from typing import Any
from unittest.mock import AsyncMock

import pytest

from qiskit_quantuminspire.qi_backend import QIBackend
from qiskit_quantuminspire.qi_provider import QIProvider
from tests.helpers import create_backend_type


@pytest.fixture
def backend_repository(mock_job_api: Any, page_reader_mock: AsyncMock) -> None:
    page_reader_mock.get_all.return_value = [
        create_backend_type(name="qi_backend_1", id=10),
        create_backend_type(name="spin", id=20),
    ]


def test_qi_provider_construct(backend_repository: Any) -> None:
    # Act
    provider = QIProvider()

    # Assert
    assert len(provider.backends()) == 2
    assert all([isinstance(backend, QIBackend) for backend in provider.backends()])


def test_get_backend_by_name(backend_repository: Any) -> None:
    # Arrange
    provider = QIProvider()

    # Act
    backend = provider.get_backend(name="qi_backend_1")

    # Assert
    assert backend.id == 10


def test_get_backend_by_id(backend_repository: Any) -> None:
    # Arrange
    provider = QIProvider()

    # Act
    backend = provider.get_backend(id=20)

    # Assert
    assert backend.name == "spin"


def test_get_backend_no_arguments_gets_first(backend_repository: Any) -> None:
    # Arrange
    provider = QIProvider()

    # Act
    backend = provider.get_backend()

    # Assert
    assert backend.id == 10


def test_get_backend_raises_value_error_if_not_found(backend_repository: Any) -> None:
    # Arrange
    provider = QIProvider()

    # Act / Assert
    with pytest.raises(ValueError):
        provider.get_backend(name="not_existing")
