from qiskit.providers.jobstatus import JobStatus
from qiskit.result.result import Result

from qiskit_quantuminspire.qi_jobs import QIBaseJob


class QIInternalJob(QIBaseJob):
    """Used as a Qiskit job for hybrid algorithms that are fully executed on the Quantum Inspire platform."""

    def status(self) -> JobStatus:
        raise NotImplementedError()

    def result(self) -> Result:
        raise NotImplementedError()
