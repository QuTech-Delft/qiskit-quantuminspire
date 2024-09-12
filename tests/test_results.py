from datetime import datetime, timezone

import pytest
from compute_api_client import BackendStatus, BackendType, Metadata, Result as JobResult
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.result.result import Result

from qiskit_quantuminspire.qi_backend import QIBackend
from qiskit_quantuminspire.qi_jobs import QIJob
from qiskit_quantuminspire.qi_results import QIResult


@pytest.fixture
def qi_backend() -> QIBackend:
    backend_type = BackendType(
        id=1,
        name="Spin 2",
        infrastructure="Hetzner",
        description="Silicon spin quantum computer",
        image_id="abcd1234",
        is_hardware=True,
        features=["multiple_measurements"],
        default_compiler_config={},
        native_gateset={"single_qubit_gates": ["X"]},
        status=BackendStatus.IDLE,
        default_number_of_shots=1024,
        max_number_of_shots=2048,
    )

    metadata = Metadata(id=1, backend_id=1, created_on=datetime.now(timezone.utc), data={"nqubits": 6})
    return QIBackend(backend_type=backend_type, metadata=metadata)


@pytest.fixture
def qi_job(qi_backend: QIBackend) -> QIJob:
    return QIJob(run_input="", backend=qi_backend, job_id="some-id")


def test_process(qi_job: QIJob) -> None:
    qi_job._job_ids = ["1"]  # The jobs in the batch job
    qi_job.job_id = "100"  # The batch job ID
    raw_results = []
    for _id in qi_job._job_ids:
        raw_results.append(
            JobResult(
                id=int(_id),
                metadata_id=1,
                created_on=datetime(2022, 10, 25, 15, 37, 54, 269823, tzinfo=timezone.utc),
                execution_time_in_seconds=1.23,
                shots_requested=100,
                shots_done=100,
                results={
                    "0000000000": 256,
                    "0000000001": 256,
                    "0000000010": 256,
                    "0000000011": 256,
                },
                job_id=int(qi_job.job_id),
            )
        )
    processed_results = QIResult(raw_results).process(qi_job)
    expected_results = Result(
        backend_name="Spin 2",
        backend_version="1.0.0",
        qobj_id="1234",
        job_id="100",
        success=True,
        results=[
            ExperimentResult(
                shots=100,
                success=True,
                meas_level=2,
                data=ExperimentResultData(counts={"0x0": 256, "0x1": 256, "0x2": 256, "0x3": 256}),
            )
        ],
        date=None,
        status=None,
        header=None,
    )
    assert processed_results.to_dict() == expected_results.to_dict()


def test_process_handles_failed_job(qi_job: QIJob) -> None:
    qi_job._job_ids = ["1"]  # The jobs in the batch job
    qi_job.job_id = "100"  # The batch job ID
    raw_results = [Exception("Bad Result")]

    processed_results = QIResult(raw_results).process(qi_job)
    expected_results = Result(
        backend_name="Spin 2",
        backend_version="1.0.0",
        qobj_id="1234",
        job_id="100",
        success=False,
        results=[
            ExperimentResult(
                shots=0,
                success=False,
                meas_level=2,
                data=ExperimentResultData(counts={}),
            )
        ],
        date=None,
        status=None,
        header=None,
    )
    assert processed_results.to_dict() == expected_results.to_dict()
