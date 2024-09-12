from typing import List

from compute_api_client import Result as RawJobResult
from qiskit.providers import JobV1 as Job
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.result.result import Result


class QIResult:
    """Handle QuantumInspire (batch job) results to integrate with Qiskit's Result interface."""

    def __init__(self, qinspire_results: List[RawJobResult]) -> None:
        self._raw_results = qinspire_results

    def process(self, job: Job) -> Result:
        """Process the raw job results obtained from QuantumInspire.

        Args:
            job: The (batch) job for which the results were obtained. While specified as `Job`
            to avoid circular dependency, it is a `QIJob`.
        Returns:
            The processed results as a Qiskit Result.
        """

        results = []
        batch_job_success = [False] * len(self._raw_results)

        for idx, result in enumerate(self._raw_results):
            counts = {}
            shots = 0
            experiment_success = False

            if isinstance(result, RawJobResult):
                shots = result.shots_done
                experiment_success = result.shots_done > 0
                counts = {hex(int(key, 2)): value for key, value in result.results.items()}
                batch_job_success[idx] = True

            experiment_data = ExperimentResultData(
                counts=counts,
            )
            experiment_result = ExperimentResult(
                shots=shots,
                success=experiment_success,
                data=experiment_data,
            )
            results.append(experiment_result)

        result = Result(
            backend_name=job.backend().name,
            backend_version="1.0.0",
            qobj_id="1234",
            job_id=job.job_id,
            success=all(batch_job_success),
            results=results,
        )
        return result
