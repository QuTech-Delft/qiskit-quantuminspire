from qiskit_quantuminspire.qi_provider import QIProvider
from qiskit_quantuminspire.qi_backend import QIBackend
from qiskit_quantuminspire.qi_jobs import QIJob
from qiskit.result.result import Result


def test_dummy() -> None:
    assert True


def test_flow() -> None:
    provider = QIProvider()
    backend = provider.get_backend("Some-Backend")
    assert isinstance(backend, QIBackend)
    job = backend.run("Some-Circuit")
    assert isinstance(job, QIJob)
    result = job.result()
    assert isinstance(result, Result)
