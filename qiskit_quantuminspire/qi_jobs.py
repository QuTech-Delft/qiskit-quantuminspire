import asyncio
from dataclasses import dataclass
from functools import cache
from typing import Any, Dict, List, Optional, Union

from compute_api_client import ApiClient, PageResult, Result as RawJobResult, ResultsApi
from qiskit.circuit import QuantumCircuit
from qiskit.providers import JobV1 as Job
from qiskit.providers.backend import Backend
from qiskit.providers.jobstatus import JobStatus
from qiskit.qobj import QobjExperimentHeader
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.result.result import Result

from qiskit_quantuminspire.api.client import config
from qiskit_quantuminspire.api.pagination import PageReader


@dataclass
class CircuitExecutionData:
    """Class for book-keeping of individual jobs."""

    circuit: QuantumCircuit
    job_id: Optional[int] = None
    results: Optional[RawJobResult] = None


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
                circuit_data.results = None if not result_item else result_item[0]

    @cache
    def result(self) -> Result:
        """Return the results of the job."""
        if not self.done():
            raise RuntimeError(f"(Batch)Job status is {self.status()}.")
        asyncio.run(self._fetch_job_results())
        return self._process_results()

    def status(self) -> JobStatus:
        """Return the status of the (batch)job, among the values of ``JobStatus``."""
        return JobStatus.DONE

    def _process_results(self) -> Result:
        """Process the raw job results obtained from QuantumInspire."""

        results = []
        batch_job_success = [False] * len(self.circuits_run_data)

        for idx, circuit_data in enumerate(self.circuits_run_data):
            qi_result = circuit_data.results
            circuit_name = circuit_data.circuit.name

            if qi_result is None:
                experiment_result = self._get_experiment_result(circuit_name=circuit_name)
                results.append(experiment_result)
                continue
            experiment_result = self._get_experiment_result(
                circuit_name=circuit_name,
                shots=qi_result.shots_done,
                counts={hex(int(key, 2)): value for key, value in qi_result.results.items()},
                experiment_success=qi_result.shots_done > 0,
            )
            results.append(experiment_result)
            batch_job_success[idx] = qi_result.shots_done > 0

        result = Result(
            backend_name=self.backend().name,
            backend_version="1.0.0",
            qobj_id="",
            job_id=self.job_id,
            success=all(batch_job_success),
            results=results,
        )
        return result

    @staticmethod
    def _get_experiment_result(
        circuit_name: str,
        shots: int = 0,
        counts: Optional[Dict[str, int]] = None,
        experiment_success: bool = False,
    ) -> ExperimentResult:
        """Create an ExperimentResult instance based on RawJobResult parameters."""
        experiment_data = ExperimentResultData(
            counts={} if counts is None else counts,
        )
        return ExperimentResult(
            shots=shots,
            success=experiment_success,
            data=experiment_data,
            header=QobjExperimentHeader(name=circuit_name),
        )
