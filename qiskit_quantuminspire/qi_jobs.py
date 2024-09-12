import asyncio
from typing import Any, List, Union

from compute_api_client import ApiClient, Result as JobResult, ResultsApi
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

    async def _fetch_job_results(self) -> List[JobResult]:
        """Fetch results for job_ids from CJM using api client."""
        results = None
        async with ApiClient(config()) as client:
            results_api = ResultsApi(client)
            result_tasks = [results_api.read_results_by_job_id_results_job_job_id_get(int(id)) for id in self._job_ids]
            results = await asyncio.gather(*result_tasks, return_exceptions=True)
        return results

    def result(self) -> Result:
        """Return the results of the job."""
        if self.status() is not JobStatus.DONE:
            raise RuntimeError(f"Job status is {self.status}.")
        raw_results = asyncio.run(self._fetch_job_results())
        processed_results = QIResult(raw_results).process(self)
        return processed_results

    def status(self) -> JobStatus:
        """Return the status of the (batch)job, among the values of ``JobStatus``."""
        return JobStatus.DONE
