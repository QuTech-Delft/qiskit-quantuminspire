import asyncio
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from compute_api_client import (
    Algorithm,
    AlgorithmIn,
    AlgorithmsApi,
    AlgorithmType,
    ApiClient,
    BatchJob,
    BatchJobIn,
    BatchJobsApi,
    BatchJobStatus,
    Commit,
    CommitIn,
    CommitsApi,
    CompileStage,
    File,
    FileIn,
    FilesApi,
    Job,
    JobIn,
    JobsApi,
    Language,
    LanguagesApi,
    PageBatchJob,
    PageResult,
    Project,
    ProjectIn,
    ProjectsApi,
    Result as RawJobResult,
    ResultsApi,
    ShareType,
)
from qiskit import qpy
from qiskit.circuit import QuantumCircuit
from qiskit.providers import JobV1
from qiskit.providers.backend import BackendV2
from qiskit.providers.jobstatus import JobStatus
from qiskit.qobj import QobjExperimentHeader
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.result.result import Result

from qiskit_quantuminspire import cqasm
from qiskit_quantuminspire.api.client import config
from qiskit_quantuminspire.api.pagination import PageReader
from qiskit_quantuminspire.api.settings import ApiSettings
from qiskit_quantuminspire.base_provider import BaseProvider


@dataclass
class CircuitExecutionData:
    """Class for book-keeping of individual jobs."""

    circuit: QuantumCircuit
    job_id: Optional[int] = None
    results: Optional[RawJobResult] = None


# Ignore type checking for QIJob due to missing Qiskit type stubs,
# which causes the base class 'Job' to be treated as 'Any'.
class QIJob(JobV1):  # type: ignore[misc]
    """A wrapper class for QuantumInspire batch jobs to integrate with Qiskit's Job interface."""

    def __init__(
        self,
        run_input: Union[QuantumCircuit, List[QuantumCircuit]],
        backend: Union[BackendV2, None],
        **kwargs: Any,
    ) -> None:
        """Initialize a QIJob instance.

        Args:
            run_input: A single/list of Qiskit QuantumCircuit object(s).
            backend: The backend on which the job is run. While specified as `Backend` to avoid
                circular dependency, it is a `QIBackend`.
            **kwargs: Additional keyword arguments passed to the parent `Job` class.
        """
        super().__init__(backend, "", **kwargs)
        self.circuits_run_data: List[CircuitExecutionData] = (
            [CircuitExecutionData(circuit=run_input)]
            if isinstance(run_input, QuantumCircuit)
            else [CircuitExecutionData(circuit=circuit) for circuit in run_input]
        )
        self.program_name = "Program created by SDK"
        self.batch_job_id: Union[int, None] = None

    def submit(self) -> None:
        asyncio.run(self._submit_async())

    async def _submit_async(self) -> None:
        """Submit the (batch)job to the quantum inspire backend.

        Use compute-api-client to call the cjm endpoints in the correct order, to submit the jobs.
        """
        options = cast(dict[str, Any], self.backend().options)
        configuration = config()
        settings = ApiSettings.from_config_file()

        # call create algorithm
        async with ApiClient(configuration) as api_client:
            language = await self._get_language(api_client, "cqasm", "3.0")
            if language is None:
                raise RuntimeError("No cqasm v3.0 language id returned by the platform")

            team_member_id = settings.auths[settings.default_host].team_member_id
            assert isinstance(team_member_id, int)

            project = await self._create_project(api_client, team_member_id)
            batch_job = await self._create_batch_job(api_client, backend_type_id=self.backend().id)

            async def job_run_sequence(
                in_api_client: ApiClient,
                in_project: Project,
                in_batch_job: BatchJob,
                circuit_data: CircuitExecutionData,
            ) -> None:
                algorithm = await self._create_algorithm(in_api_client, in_project.id)
                commit = await self._create_commit(in_api_client, algorithm.id)
                file = await self._create_file(in_api_client, commit.id, language.id, circuit_data.circuit)
                job: Job = await self._create_job(
                    in_api_client,
                    file.id,
                    in_batch_job.id,
                    number_of_shots=options.get("shots", self.backend().default_shots),
                )
                circuit_data.job_id = job.id

            # iterate over the circuits
            run_coroutines = (
                job_run_sequence(api_client, project, batch_job, circuit_run_data)
                for circuit_run_data in self.circuits_run_data
            )
            await asyncio.gather(*run_coroutines)
            await self._enqueue_batch_job(api_client, batch_job.id)
            self.batch_job_id = batch_job.id

    async def _create_project(self, api_client: ApiClient, owner_id: int) -> Project:
        api_instance = ProjectsApi(api_client)
        obj = ProjectIn(
            owner_id=owner_id,
            name=self.program_name,
            description="Project created by SDK",
            starred=False,
        )
        return await api_instance.create_project_projects_post(obj)

    async def _create_algorithm(self, api_client: ApiClient, project_id: int) -> Algorithm:
        api_instance = AlgorithmsApi(api_client)
        obj = AlgorithmIn(
            project_id=project_id, type=AlgorithmType.QUANTUM, shared=ShareType.PRIVATE, name=self.program_name
        )
        return await api_instance.create_algorithm_algorithms_post(obj)

    async def _create_commit(self, api_client: ApiClient, algorithm_id: int) -> Commit:
        api_instance = CommitsApi(api_client)
        obj = CommitIn(
            description="Commit created by SDK",
            algorithm_id=algorithm_id,
        )
        return await api_instance.create_commit_commits_post(obj)

    async def _create_file(
        self, api_client: ApiClient, commit_id: int, language_id: int, circuit: QuantumCircuit
    ) -> File:
        api_instance = FilesApi(api_client)
        obj = FileIn(
            commit_id=commit_id,
            content=cqasm.dumps(circuit),
            language_id=language_id,
            compile_stage=CompileStage.NONE,
            compile_properties={},
        )
        return await api_instance.create_file_files_post(obj)

    async def _create_batch_job(self, api_client: ApiClient, backend_type_id: int) -> BatchJob:
        api_instance = BatchJobsApi(api_client)
        obj = BatchJobIn(backend_type_id=backend_type_id)
        return await api_instance.create_batch_job_batch_jobs_post(obj)

    async def _create_job(
        self, api_client: ApiClient, file_id: int, batch_job_id: int, number_of_shots: Optional[int] = None
    ) -> Job:
        api_instance = JobsApi(api_client)
        obj = JobIn(file_id=file_id, batch_job_id=batch_job_id, number_of_shots=number_of_shots)
        return await api_instance.create_job_jobs_post(obj)

    async def _enqueue_batch_job(self, api_client: ApiClient, batch_job_id: int) -> BatchJob:
        api_instance = BatchJobsApi(api_client)
        return await api_instance.enqueue_batch_job_batch_jobs_id_enqueue_patch(batch_job_id)

    async def _get_language(
        self, api_client: ApiClient, language_name: str, language_version: str
    ) -> Union[Language, None]:
        language_api_instance = LanguagesApi(api_client)
        languages_page = await language_api_instance.read_languages_languages_get()
        for lan in languages_page.items:
            if language_name.lower() == lan.name.lower():
                if language_version == lan.version:
                    return lan

        return None

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

        # mapping of QI2 BatchJobStatus to Qiskit JobStatus
        status_map = {
            BatchJobStatus.QUEUED: JobStatus.QUEUED,
            BatchJobStatus.RESERVED: JobStatus.QUEUED,
            BatchJobStatus.PLANNED: JobStatus.QUEUED,
            BatchJobStatus.RUNNING: JobStatus.RUNNING,
            BatchJobStatus.FINISHED: JobStatus.DONE,
        }

        batch_job = asyncio.run(self._fetch_batchjob_status())
        return status_map[batch_job.status]

    async def _fetch_batchjob_status(self) -> BatchJob:
        async with ApiClient(config()) as api_client:
            api_instance = BatchJobsApi(api_client)

            page_reader = PageReader[PageBatchJob, BatchJob]()
            batch_job = await page_reader.get_single(api_instance.read_batch_jobs_batch_jobs_get, id=self.batch_job_id)
            if batch_job is None:
                raise RuntimeError(f"No (batch)job with id {self.batch_job_id}")

            return batch_job

    def serialize(self, file_path: Union[str, Path]) -> None:
        """Serialize job information in this class to a file.

        Uses Qiskit serialization to write circuits to a .qpy file, and includes
        backend and and batch_job information in the metadata so that we can recover
        the associated data later.

        Args:
            file_path: The path to the file where the job information will be stored.
        """
        if len(self.circuits_run_data) == 0:
            raise ValueError("No circuits to serialize")

        with open(file_path, "wb") as file:
            for circuit_data in self.circuits_run_data:
                circuit_data.circuit.metadata["job_id"] = circuit_data.job_id
                circuit_data.circuit.metadata["backend_type_name"] = self.backend().name
                circuit_data.circuit.metadata["backend_type_id"] = self.backend().id
                circuit_data.circuit.metadata["batch_job_id"] = self.batch_job_id

            qpy.dump([circuit_data.circuit for circuit_data in self.circuits_run_data], file)

    @classmethod
    def deserialize(cls, provider: BaseProvider, file_path: Union[str, Path]) -> "QIJob":
        """Recover a prior job from a file written by QIJob.serialize().

        Args:
            provider: Used to get the backend on which the original job ran.
            file_path: The path to the file where the job information is stored.
        """
        with open(file_path, "rb") as file:
            circuits = qpy.load(file)

            # Qiskit doesn't seem to allow serialization of an empty list of circuits
            assert len(circuits) > 0

            try:
                backend_name = cast(str, circuits[0].metadata["backend_type_name"])
                backend_id = cast(int, circuits[0].metadata["backend_type_id"])
                batch_job_id = cast(int, circuits[0].metadata["batch_job_id"])
            except KeyError:
                raise ValueError(f"Invalid file format: {file_path}")

            circuits = cast(list[QuantumCircuit], circuits)

            job = cls(circuits, provider.get_backend(backend_name, backend_id))
            job.batch_job_id = batch_job_id

            for circuit_data in job.circuits_run_data:
                circuit_data.job_id = circuit_data.circuit.metadata.get("job_id")

            return job

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
            job_id=str(self.batch_job_id),
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
