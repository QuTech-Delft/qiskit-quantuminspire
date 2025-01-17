from typing import Generator
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from qiskit.providers.models.backendstatus import BackendStatus

from qiskit_quantuminspire.hybrid.hybrid_backend import QIHybridBackend


@pytest.fixture()
def qi_hybrid_job_mock(mocker: MockerFixture) -> Generator[MagicMock, None, None]:
    job = MagicMock()
    job.submit = MagicMock()
    mocker.patch("qiskit_quantuminspire.hybrid.hybrid_backend.QIHybridJob", return_value=job)
    yield job
    job.submit.reset_mock()


def test_status(quantum_interface: MagicMock) -> None:
    backend = QIHybridBackend(quantum_interface)
    # Exact BackendStatus is not important
    assert type(backend.status) is BackendStatus


def test_submit(quantum_interface: MagicMock, qi_hybrid_job_mock: MagicMock) -> None:
    backend = QIHybridBackend(quantum_interface)
    backend.run([])
    qi_hybrid_job_mock.submit.assert_called_once()
