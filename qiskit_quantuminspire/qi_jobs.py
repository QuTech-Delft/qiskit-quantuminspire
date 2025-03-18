import asyncio
import warnings
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from colorama import Fore, Style
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
    JobStatus as QIJobStatus,
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
from qi2_shared.client import config
from qi2_shared.pagination import PageReader
from qi2_shared.settings import ApiSettings
from qi2_shared.utils import run_async
from qiskit import qpy
from qiskit.circuit import QuantumCircuit
from qiskit.providers import JobV1
from qiskit.providers.backend import BackendV2
from qiskit.providers.jobstatus import JobStatus
from qiskit.qobj import QobjExperimentHeader
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.result.result import Result

from qiskit_quantuminspire import cqasm
from qiskit_quantuminspire.base_provider import BaseProvider


class ExperimentFailedWarning(UserWarning):
    pass


@dataclass
class CircuitExecutionData:
    """Class for book-keeping of individual jobs."""

    circuit: QuantumCircuit
    job_id: Optional[int] = None
    results: Optional[RawJobResult] = None
    system_message: Optional[Dict[str, str]] = None


# Ignore type checking for QIBaseJob due to missing Qiskit type stubs,
# which causes the base class 'Job' to be treated as 'Any'.
class QIBaseJob(JobV1):  # type: ignore[misc]
    circuits_run_data: List[CircuitExecutionData]

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
        self.circuits_run_data = []
        self._add_circuits(run_input)
        self.program_name = "Program created by SDK"
        self.batch_job_id: Union[int, None] = None

    def _add_circuits(self, circuits: Union[QuantumCircuit, List[QuantumCircuit]]) -> None:
        """Add circuits to the list of circuits to be run."""
        circuits = [circuits] if isinstance(circuits, QuantumCircuit) else circuits
        self.circuits_run_data.extend([CircuitExecutionData(circuit=circuit) for circuit in circuits])

    def _process_results(self) -> Result:
        """Process the raw job results obtained from QuantumInspire."""

        results = []
        batch_job_success = [False] * len(self.circuits_run_data)
        failed_experiments = dict()

        for idx, circuit_data in enumerate(self.circuits_run_data):
            qi_result = circuit_data.results
            circuit_name = circuit_data.circuit.name
            num_qubits = circuit_data.circuit.num_qubits
            num_clbits = circuit_data.circuit.num_clbits
            num_bits = num_qubits if (num_clbits == 0) else num_clbits
            exp_header = QobjExperimentHeader(name=circuit_name, memory_slots=num_bits)

            if qi_result is None:
                assert circuit_data.system_message is not None
                failed_experiments[circuit_name] = circuit_data.system_message
                trace_id = circuit_data.system_message.get("trace_id", "")
                error_message = circuit_data.system_message.get("message", "")
                experiment_result = self._create_empty_experiment_result(
                    exp_header=exp_header, trace_id=trace_id, message=error_message
                )
                results.append(experiment_result)
                continue

            experiment_result = self._create_experiment_result(
                exp_header=exp_header,
                result=qi_result,
            )
            results.append(experiment_result)
            batch_job_success[idx] = qi_result.shots_done > 0

        if failed_experiments:
            warning_message = (
                f"\n{Fore.YELLOW}Some experiments {Fore.RED}FAILED. "
                f"{Fore.YELLOW}You can view the detailed system messages \n"
                f"in the 'system_messages' attribute of the result object. "
                f"\nFor e.g: result.system_messages.{Style.RESET_ALL}"
            )
            warnings.warn(warning_message, category=ExperimentFailedWarning)

        result = Result(
            backend_name=self.backend().name,
            backend_version="1.0.0",
            qobj_id="",
            job_id=str(self.batch_job_id),
            success=all(batch_job_success),
            results=results,
            status="Result successful" if all(batch_job_success) else "Result failed",
            system_messages=failed_experiments,
        )
        return result

    @staticmethod
    def _create_experiment_result(
        exp_header: QobjExperimentHeader,
        result: RawJobResult,
    ) -> ExperimentResult:
        """Create an ExperimentResult instance based on RawJobResult parameters."""
        counts = {hex(int(key, 2)): value for key, value in result.results.items()}
        memory = [hex(int(measurement, 2)) for measurement in result.raw_data] if result.raw_data else None

        experiment_data = ExperimentResultData(
            counts={} if counts is None else counts,
            memory=memory,
        )
        return ExperimentResult(
            shots=result.shots_done,
            success=result.shots_done > 0,
            data=experiment_data,
            header=exp_header,
            status="Experiment successful",
        )

    @staticmethod
    def _create_empty_experiment_result(
        exp_header: QobjExperimentHeader, trace_id: Optional[str], message: Optional[str]
    ) -> ExperimentResult:
        """Create an empty ExperimentResult instance."""
        return ExperimentResult(
            shots=0,
            success=False,
            data=ExperimentResultData(counts={}),
            header=exp_header,
            status=f"Experiment failed. Trace_id: {trace_id}, System Message: {message}",
        )


class QIJob(QIBaseJob):
    """A wrapper class for QuantumInspire batch jobs to integrate with Qiskit's Job interface."""

    def submit(self) -> None:
        run_async(self._submit_async())

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
                    raw_data_enabled=cast(bool, options.get("memory")),
                    number_of_shots=options.get("shots"),
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
            name=circuit.name,
        )
        return await api_instance.create_file_files_post(obj)

    async def _create_batch_job(self, api_client: ApiClient, backend_type_id: int) -> BatchJob:
        api_instance = BatchJobsApi(api_client)
        obj = BatchJobIn(backend_type_id=backend_type_id)
        return await api_instance.create_batch_job_batch_jobs_post(obj)

    async def _create_job(
        self,
        api_client: ApiClient,
        file_id: int,
        batch_job_id: int,
        raw_data_enabled: bool,
        number_of_shots: Optional[int] = None,
    ) -> Job:
        api_instance = JobsApi(api_client)
        obj = JobIn(
            file_id=file_id,
            batch_job_id=batch_job_id,
            number_of_shots=number_of_shots,
            raw_data_enabled=raw_data_enabled,
        )
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
            job_ids_to_check = []

            for circuit_data, result_item in zip(self.circuits_run_data, result_items):
                circuit_data.results = None if not result_item else result_item[0]
                if circuit_data.results is None:
                    assert circuit_data.job_id is not None
                    job_ids_to_check.append(circuit_data.job_id)

            if job_ids_to_check:
                await self._fetch_failed_jobs_message(client, job_ids_to_check)

    async def _fetch_failed_jobs_message(self, api_client: ApiClient, job_ids_to_check: List[int]) -> None:
        """Fetch messages for failed jobs and update circuit data accordingly.

        Args:
            api_client: The API client for job communication.
            job_ids_to_check: List of job IDs that need to be inspected.
        """

        jobs_api = JobsApi(api_client)

        job_tasks = [jobs_api.read_job_jobs_id_get(id=_id) for _id in job_ids_to_check]

        jobs: List[Job] = await asyncio.gather(*job_tasks)

        failed_job_id_to_message = {
            job.id: {
                "message": job.message if job.status == QIJobStatus.FAILED else "No Results",
                "trace_id": job.trace_id,
            }
            for job in jobs
        }

        for circuit_data in self.circuits_run_data:
            if circuit_data.job_id in failed_job_id_to_message:
                circuit_data.system_message = failed_job_id_to_message[circuit_data.job_id]

    def status(self) -> JobStatus:
        """Return the status of the (batch)job, among the values of ``JobStatus``."""

        # mapping of QI BatchJobStatus to Qiskit JobStatus
        status_map = {
            BatchJobStatus.QUEUED: JobStatus.QUEUED,
            BatchJobStatus.RESERVED: JobStatus.QUEUED,
            BatchJobStatus.PLANNED: JobStatus.QUEUED,
            BatchJobStatus.RUNNING: JobStatus.RUNNING,
            BatchJobStatus.FINISHED: JobStatus.DONE,
        }

        batch_job = run_async(self._fetch_batchjob_status())
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

    @cache
    def result(self, wait_for_results: bool = True, timeout: float = 60.0) -> Result:
        """Return the results of the job."""
        if wait_for_results:
            self.wait_for_final_state(timeout=timeout)
        elif not self.done():
            raise RuntimeError(f"(Batch)Job status is {self.status()}.")
        run_async(self._fetch_job_results())
        return self._process_results()
