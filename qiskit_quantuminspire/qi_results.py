from qiskit.providers import JobV1 as Job
from qiskit.qobj import QobjExperimentHeader
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.result.result import Result


class QIResult:
    """Handle QuantumInspire (batch job) results to integrate with Qiskit's Result interface."""

    def __init__(self, job: Job) -> None:
        """Initialize the result processor for QuantumInspire job results.

        Args:
            job: The (batch) job for which the results were obtained. While specified as `Job`
                to avoid circular dependency, it is a `QIJob`.
        Returns:
            None.
        """

        self._job = job  # The batch job

    def process(self) -> Result:
        """Process the raw job results obtained from QuantumInspire."""

        results = []
        batch_job_success = [False] * len(self._job.circuits_run_data)

        for idx, ciruit_data in enumerate(self._job.circuits_run_data):
            result_header = QobjExperimentHeader(name=ciruit_data.circuit.name)
            circuit_results = ciruit_data.results

            if not circuit_results:
                # For failed job, there are no results
                experiment_data = ExperimentResultData(
                    counts={},
                )
                experiment_result = ExperimentResult(
                    shots=0,
                    success=False,
                    data=experiment_data,
                    header=result_header,
                )
                results.append(experiment_result)
            else:
                results_valid = [False] * len(circuit_results)
                for idx_res, result in enumerate(circuit_results):
                    shots = result.shots_done
                    experiment_success = result.shots_done > 0
                    counts = {hex(int(key, 2)): value for key, value in result.results.items()}
                    results_valid[idx_res] = experiment_success

                    experiment_data = ExperimentResultData(
                        counts=counts,
                    )
                    experiment_result = ExperimentResult(
                        shots=shots,
                        success=experiment_success,
                        data=experiment_data,
                        header=result_header,
                    )
                    results.append(experiment_result)
                batch_job_success[idx] = all(results_valid)

        result = Result(
            backend_name=self._job.backend().name,
            backend_version="1.0.0",
            qobj_id="",
            job_id=self._job.job_id,
            success=all(batch_job_success),
            results=results,
        )
        return result
