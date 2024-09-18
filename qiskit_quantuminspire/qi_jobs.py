import asyncio
from typing import Any, List, Union

from compute_api_client import ApiClient, PageResult, Result as RawJobResult, ResultsApi
from qiskit.circuit import QuantumCircuit
from qiskit.providers import JobV1 as Job
from qiskit.providers.backend import Backend
from qiskit.providers.jobstatus import JobStatus
from qiskit.result.result import Result

from qiskit_quantuminspire.api.client import config
from qiskit_quantuminspire.api.pagination import PageReader
from qiskit_quantuminspire.qi_results import QIResult


class CircuitExecutionData:
    """Class for bookkeping of individual jobs."""

    def __init__(
        self, circuit: QuantumCircuit, job_id: Union[int, None] = None, results: Union[List[RawJobResult], None] = None
    ) -> None:
        self.job_id = job_id
        self.circuit = circuit
        self.results = [] if results is None else results


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
            run_input: A single/list of Qiskit QuantumCircuit object(s).
            backend: The backend on which the job is run. While specified as `Backend` to avoid
                circular dependency, it is a `QIBackend`.
            job_id: A unique identifier for the (batch)job.
            **kwargs: Additional keyword arguments passed to the parent `Job` class.
        """
        super().__init__(backend, job_id, **kwargs)
        self._cached_result: Union[Result, None] = None
        self.circuits_run_data: List[CircuitExecutionData] = (
            [CircuitExecutionData(circuit=run_input)]
            if isinstance(run_input, QuantumCircuit)
            else [CircuitExecutionData(circuit=circuit) for circuit in run_input]
        )

    def submit(self) -> None:
        """Submit the (batch)job to the quantum inspire backend.

        Use compute-api-client to call the cjm endpoints in the correct order, to submit the jobs.
        """
        # Here, we will update the self.circuits_run_data and attach the job ids for each circuit
        for _ in range(1, 3):
            pass
        self.job_id = "999"  # ID of the submitted batch-job

    async def _fetch_job_results(self) -> None:
        """Fetch results for job_ids from CJM using api client."""
        async with ApiClient(config()) as client:
            page_reader = PageReader[PageResult, RawJobResult]()
            results_api = ResultsApi(client)
            pagination_handler = page_reader.get_all
            results_handler = results_api.read_results_by_job_id_results_job_job_id_get

            result_tasks = [
                pagination_handler(results_handler, job_id=circuit_data.job_id)
                for circuit_data in self.circuits_run_data
            ]
            result_items = await asyncio.gather(*result_tasks)

            for circuit_data, result_item in zip(self.circuits_run_data, result_items):
                circuit_data.results = result_item

    def result(self) -> Result:
        """Return the results of the job."""
        if not self.done():
            raise RuntimeError(f"(Batch)Job status is {self.status()}.")
        if self._cached_result:
            return self._cached_result
        asyncio.run(self._fetch_job_results())
        self._cached_result = QIResult(self).process()
        return self._cached_result

    def status(self) -> JobStatus:
        """Return the status of the (batch)job, among the values of ``JobStatus``."""
        return JobStatus.DONE
