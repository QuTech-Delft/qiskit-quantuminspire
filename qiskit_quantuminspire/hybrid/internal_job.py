from qiskit.providers.jobstatus import JobStatus
from qiskit.result.result import Result

from qiskit_quantuminspire.qi_jobs import QIBaseJob


class QIInternalJob(QIBaseJob):
    def status(self) -> JobStatus:
        raise NotImplementedError()

    def result(self) -> Result:
        raise NotImplementedError()
