from datetime import datetime, timezone

from compute_api_client import Result as RawJobResult
from qiskit import QuantumCircuit
from qiskit.qobj import QobjExperimentHeader
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.result.result import Result

from qiskit_quantuminspire.qi_jobs import QIJob
from qiskit_quantuminspire.qi_results import QIResult
from tests.helpers import create_backend_type


def test_process() -> None:
    qi_backend = create_backend_type(name="qi_backend_1")
    qc = QuantumCircuit(2, 2)

    qi_job = QIJob(run_input=qc, backend=qi_backend, job_id="some-id")
    batch_job_id = "100"
    qi_job.job_id = batch_job_id
    individual_job_id = 1
    qi_job.circuits_run_data[0].job_id = individual_job_id
    raw_results = [
        RawJobResult(
            id=individual_job_id,
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
    ]
    qi_job.circuits_run_data[0].results = raw_results
    processed_results = QIResult(qi_job).process()
    experiment_data = ExperimentResultData(counts={"0x0": 256, "0x1": 256, "0x2": 256, "0x3": 256})
    experiment_result = ExperimentResult(
        shots=100,
        success=True,
        meas_level=2,
        data=experiment_data,
        header=QobjExperimentHeader(name=qi_job.circuits_run_data[0].circuit.name),
    )
    expected_results = Result(
        backend_name="qi_backend_1",
        backend_version="1.0.0",
        qobj_id="",
        job_id=batch_job_id,
        success=True,
        results=[experiment_result],
        date=None,
        status=None,
        header=None,
    )
    assert processed_results.to_dict() == expected_results.to_dict()
    assert processed_results.data(qc) == experiment_data.to_dict()


def test_process_handles_failed_job() -> None:

    qi_backend = create_backend_type(name="qi_backend_1")
    qc = QuantumCircuit(2, 2)

    qi_job = QIJob(run_input=qc, backend=qi_backend, job_id="some-id")
    batch_job_id = "100"
    qi_job.job_id = batch_job_id
    individual_job_id = 1
    qi_job.circuits_run_data[0].job_id = individual_job_id

    qi_job.circuits_run_data[0].results = []

    processed_results = QIResult(qi_job).process()
    expected_results = Result(
        backend_name="qi_backend_1",
        backend_version="1.0.0",
        qobj_id="",
        job_id=batch_job_id,
        success=False,
        results=[
            ExperimentResult(
                shots=0,
                success=False,
                meas_level=2,
                data=ExperimentResultData(counts={}),
                header=QobjExperimentHeader(name=qi_job.circuits_run_data[0].circuit.name),
            )
        ],
        date=None,
        status=None,
        header=None,
    )
    assert processed_results.to_dict() == expected_results.to_dict()
