import asyncio
from typing import List, Union
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from qiskit import QuantumCircuit

from qiskit_quantuminspire.qi_jobs import QIJob


def test_result(mocker: MockerFixture) -> None:

    qc = QuantumCircuit(2, 2)

    job = QIJob(run_input=qc, backend=None, job_id="some-id")

    mocker.patch.object(job, "done", return_value=True)

    mock_fetch_job_results = AsyncMock(return_value=MagicMock())
    mocker.patch.object(job, "_fetch_job_results", mock_fetch_job_results)

    mock_process = mocker.patch(
        "qiskit_quantuminspire.qi_jobs.QIResult.process",
        return_value=MagicMock(),
    )

    for _ in range(4):  # Check caching
        job.result()

    mock_process.assert_called_once()
    mock_fetch_job_results.assert_called_once()


def test_result_raises_error_when_status_not_done(mocker: MockerFixture) -> None:
    job = QIJob(run_input="", backend=None, job_id="some-id")
    mocker.patch.object(job, "done", return_value=False)
    with pytest.raises(RuntimeError):
        job.result()


@pytest.mark.parametrize(
    "circuits, expected_n_jobs",
    [
        (QuantumCircuit(1, 1), 1),  # Single circuit
        ([QuantumCircuit(1, 1), QuantumCircuit(2, 2)], 2),  # List of circuits
    ],
)
def test_fetch_job_result(
    mocker: MockerFixture,
    page_reader_mock: MockerFixture,
    circuits: Union[QuantumCircuit, List[QuantumCircuit]],
    expected_n_jobs: int,
) -> None:

    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.config",
        return_value=MagicMock(),
    )
    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.ApiClient",
        autospec=True,
    )

    mocker.patch(
        "qiskit_quantuminspire.qi_jobs.ResultsApi",
        autospec=True,
    )

    page_reader_mock.get_all.side_effect = [[MagicMock()] for _ in range(expected_n_jobs)]

    job = QIJob(run_input=circuits, backend=None, job_id="some-id")

    asyncio.run(job._fetch_job_results())

    assert len(job.circuits_run_data) == expected_n_jobs

    assert all(circuit_data.results for circuit_data in job.circuits_run_data)

