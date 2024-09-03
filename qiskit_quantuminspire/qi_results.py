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

        for result in self._raw_results:
            experiment_result = ExperimentResult(
                shots=result.shots_done,
                success=True,
                data=ExperimentResultData(),
            )
            results.append(experiment_result)

        result = Result(
            backend_name=job.backend().name,
            backend_version="1.0.0",
            qobj_id=1234,
            job_id=job.job_id,
            success=True,
            results=results,
        )
        return result
