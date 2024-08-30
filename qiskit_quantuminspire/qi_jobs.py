from qiskit.providers import JobV1 as Job
from qiskit.providers.backend import Backend
from qiskit.result.result import Result
from qiskit.providers.jobstatus import JobStatus
from compute_api_client import Result as JobResult
from typing import Any, List
from datetime import datetime, timezone
from qiskit_quantuminspire.qi_results import QIResult


class QIJob(Job):
    """A wrapper class for QuantumInspire batch jobs to integrate with Qiskit's Job interface."""

    def __init__(self, run_input: Any, backend: Backend | None, job_id: str, **kwargs) -> None:
        """
        Initialize a QIJob instance.

        Args:
            run_input: A single/list of Qiskit QuantumCircuit objects or hybrid algorithms.
            backend: The backend on which the job is run. While specified as `Backend` to avoid
                circular dependency, it is a `QIBackend`.
            job_id: A unique identifier for the (batch)job.
            **kwargs: Additional keyword arguments passed to the parent `Job` class.
        """
        super().__init__(backend, job_id, **kwargs)
        self._job_ids = []
        self._run_input = run_input

    def submit(self):
        """Submit the (batch)job to the quantum inspire backend.

        Use compute-api-client to call the cjm endpoints in the correct order, to submit the jobs.
        """
        for i in range(1, 3):
            self._job_ids.append(i)
        self.job_id = 999  # ID of the submitted batch-job

    def _fetch_job_results(self) -> List[JobResult]:
        """Fetch results for job_ids from CJM using api client"""
        raw_results = []
        for job_id in self._job_ids:
            job_result = JobResult(
                id=job_id,
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
                job_id=job_id,
            )
            raw_results.append(job_result)
        return raw_results

    def result(self) -> Result:
        """Return the results of the job."""
        raw_results = self._fetch_job_results()
        processed_results = QIResult(raw_results).process(self)
        return processed_results

    def status(self) -> JobStatus:
        """Return the status of the (batch)job, among the values of ``JobStatus``."""
        return JobStatus.DONE
