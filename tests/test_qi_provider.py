import logging
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from qiskit_quantuminspire.qi_backend import QIBackend
from qiskit_quantuminspire.qi_provider import QIProvider
from tests.helpers import create_backend_type


@pytest.fixture
def backend_repository(mocker: MockerFixture, mock_job_api: Any, page_reader_mock: AsyncMock) -> None:
    mocker.patch("qiskit_quantuminspire.qi_provider.config")
    mocker.patch("qiskit_quantuminspire.qi_provider.ApiClient")
    mock_run_async = mocker.patch("qiskit_quantuminspire.qi_backend.run_async")
    mock_run_async.return_value = create_backend_type()
    page_reader_mock.get_all.return_value = [
        create_backend_type(name="qi_backend_1", id=10),
        create_backend_type(name="spin", id=20),
    ]


def test_qi_provider_construct(backend_repository: None) -> None:
    # Act
    provider = QIProvider()

    # Assert
    assert len(provider.backends()) == 2
    assert all([isinstance(backend, QIBackend) for backend in provider.backends()])


def test_get_backend_by_name(backend_repository: None) -> None:
    # Arrange
    provider = QIProvider()

    # Act
    backend = provider.get_backend(name="qi_backend_1")

    # Assert
    assert backend.id == 10


def test_get_backend_by_id(backend_repository: None) -> None:
    # Arrange
    provider = QIProvider()

    # Act
    backend = provider.get_backend(id=20)

    # Assert
    assert backend.name == "spin"


def test_get_backend_no_arguments_gets_first(backend_repository: None) -> None:
    # Arrange
    provider = QIProvider()

    # Act
    backend = provider.get_backend()

    # Assert
    assert backend.id == 10


def test_get_backend_print_message(backend_repository: None, caplog: Any) -> None:
    # Arrange
    provider = QIProvider()

    # Act
    with caplog.at_level(logging.WARNING):
        provider.get_backend(name="qi_backend_1")

    # Assert
    assert len(caplog.records) == 1
    assert "backend: message for backend" in caplog.text


@pytest.mark.parametrize("name,id", [("not_existing", None), (None, 6), ("not_existing", 6)])
def test_get_backend_raises_value_error_if_not_found(name: str, id: int, backend_repository: None) -> None:
    # Arrange
    provider = QIProvider()

    # Act / Assert
    with pytest.raises(ValueError):
        provider.get_backend(name="not_existing")
