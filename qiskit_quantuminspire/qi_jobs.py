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

    async def submit(self) -> None:
        """Submit the (batch)job to the quantum inspire backend.

        Use compute-api-client to call the cjm endpoints in the correct order, to submit the jobs.
        """
        options = self.backend().options
        # call create algorithm
        async with ApiClient(config()) as api_client:
            project = await self._create_project(api_client)
            algorithm = await self._create_algorithm(api_client, project)
            commit = await self._create_commit(api_client, algorithm)
            file = await self._create_file(api_client, commit)
            batch_job = await self._create_batch_job(api_client, backend_type_id=self.backend().id)
            job: Job = await self._create_job(
                api_client, file, batch_job, number_of_shots=options.get("shots", default=1000)
            )
            await self._enqueue_batch_job(api_client, batch_job)
            self.job_id = job.id  # TODO: this is also provided in the constructor. Why?

    async def _create_project(self, api_client: ApiClient) -> Project:
        api_instance = ProjectsApi(api_client)
        obj = ProjectIn(
            owner_id=self.auth_settings.owner_id,
            name=self.program_name,
            description="Project created by SDK",
            starred=False,
        )
        return await api_instance.create_project_projects_post(obj)

    async def _create_algorithm(self, api_client: ApiClient, project: Project) -> Algorithm:
        api_instance = AlgorithmsApi(api_client)
        obj = AlgorithmIn(
            project_id=project.id, type=AlgorithmType.QUANTUM, shared=ShareType.PRIVATE, name=self.program_name
        )
        return await api_instance.create_algorithm_algorithms_post(obj)

    async def _create_commit(self, api_client: ApiClient, algorithm: Algorithm) -> Commit:
        api_instance = CommitsApi(api_client)
        obj = CommitIn(
            description="Commit created by SDK",
            algorithm_id=algorithm.id,
        )
        return await api_instance.create_commit_commits_post(obj)

    async def _create_file(self, api_client: ApiClient, commit: Commit) -> File:
        api_instance = FilesApi(api_client)
        obj = FileIn(
            commit_id=commit.id,
            content="",  # TODO: the cQasm
            language_id=1,
            compile_stage=CompileStage.NONE,
            compile_properties={},
        )
        return await api_instance.create_file_files_post(obj)

    async def _create_batch_job(self, api_client: ApiClient, backend_type_id: int) -> BatchJob:
        api_instance = BatchJobsApi(api_client)
        obj = BatchJobIn(backend_type_id=backend_type_id)
        return await api_instance.create_batch_job_batch_jobs_post(obj)

    async def _create_job(
        self, api_client: ApiClient, file: File, batch_job: BatchJob, number_of_shots: Optional[int] = None
    ) -> Job:
        api_instance = JobsApi(api_client)
        obj = JobIn(file_id=file.id, batch_job_id=batch_job.id, number_of_shots=number_of_shots)
        return await api_instance.create_job_jobs_post(obj)

    async def _enqueue_batch_job(self, api_client: ApiClient, batch_job: BatchJob) -> BatchJob:
        api_instance = BatchJobsApi(api_client)
        return await api_instance.enqueue_batch_job_batch_jobs_id_enqueue_patch(batch_job.id)

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
