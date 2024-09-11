from datetime import datetime, timezone
from typing import Any, List, Union

from compute_api_client import ApiClient, BatchJob, BatchJobsApi, BatchJobStatus, Result as JobResult
from qiskit.circuit import QuantumCircuit
from qiskit.providers import JobV1 as Job
from qiskit.providers.backend import Backend
from qiskit.providers.jobstatus import JobStatus
from qiskit.result.result import Result

from qiskit_quantuminspire.api.client import config
from qiskit_quantuminspire.qi_results import QIResult


# Ignore type checking for QIJob due to missing Qiskit type stubs,
# which causes the base class 'Job' to be treated as 'Any'.
class QIJob(Job):  # type: ignore[misc]
    """A wrapper class for QuantumInspire batch jobs to integrate with Qiskit's Job interface."""

    def __init__(
        self,
        run_input: Union[QuantumCircuit, List[QuantumCircuit]],
        backend: Union[Backend, None],
        job_id: str,
        **kwargs: Any,
    ) -> None:
        """Initialize a QIJob instance.

        Args:
            run_input: A single/list of Qiskit QuantumCircuit objects or hybrid algorithms.
            backend: The backend on which the job is run. While specified as `Backend` to avoid
                circular dependency, it is a `QIBackend`.
            job_id: A unique identifier for the (batch)job.
            **kwargs: Additional keyword arguments passed to the parent `Job` class.
        """
        super().__init__(backend, job_id, **kwargs)
        self._job_ids: List[str] = []
        self._run_input = run_input

    def submit(self) -> None:
        """Submit the (batch)job to the quantum inspire backend.

        Use compute-api-client to call the cjm endpoints in the correct order, to submit the jobs.
        """
        for i in range(1, 3):
            self._job_ids.append(str(i))
        self.job_id = "999"  # ID of the submitted batch-job

    def _fetch_job_results(self) -> List[JobResult]:
        """Fetch results for job_ids from CJM using api client."""
        raw_results = []
        for job_id in self._job_ids:
            job_result = JobResult(
                id=int(job_id),
                metadata_id=1,
                created_on=datetime(2022, 10, 25, 15, 37, 54, 269823, tzinfo=timezone.utc),
                execution_time_in_seconds=1.23,
                shots_requested=100,
                shots_done=100,
                results={
                    "0000000000": 0.270000,
                    "0000000001": 0.260000,
                    "0000000010": 0.180000,
                    "0000000011": 0.290000,
                },
                job_id=int(job_id),
            )
            raw_results.append(job_result)
        return raw_results

    def result(self) -> Result:
        """Return the results of the job."""
        raw_results = self._fetch_job_results()
        processed_results = QIResult(raw_results).process(self)
        return processed_results

    async def status(self) -> JobStatus:
        """Return the status of the (batch)job, among the values of ``JobStatus``."""
        async with ApiClient(config()) as client:
            api_instance = BatchJobsApi(client)
            batch_jobs: List[BatchJob] = api_instance.read_batch_jobs_batch_jobs_get(job_id=self.job_id).items

            match batch_jobs[0].status:
                case BatchJobStatus.QUEUED | BatchJobStatus.RESERVED | BatchJobStatus.PLANNED:
                    return JobStatus.QUEUED
                case BatchJobStatus.RUNNING:
                    return JobStatus.RUNNING
                case BatchJobStatus.FINISHED:
                    return JobStatus.DONE
                case _:
                    return JobStatus.ERROR
