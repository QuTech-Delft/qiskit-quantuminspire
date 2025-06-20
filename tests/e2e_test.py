import argparse
import math

from qiskit import QuantumCircuit

from qiskit_quantuminspire.qi_instructions import Asm
from qiskit_quantuminspire.qi_provider import QIProvider


def _run_e2e_tests(name: str) -> None:
    num_qubits = 3
    qc = QuantumCircuit(num_qubits)
    qc.h(0)
    qc.append(Asm(backend_name="TestBackend", asm_code=""" a ' " {} () [] b """))
    qc.x(1)
    qc.y(2)
    qc.cx(0, 1)
    qc.z(1)
    qc.s(0)
    qc.rx(math.pi / 2, 0)
    qc.ry(math.pi / 2, 1)
    qc.rz(math.pi / 2, 2)
    qc.sdg(2)
    qc.t(1)
    qc.tdg(0)
    qc.cz(1, 2)
    qc.cp(math.pi / 2, 1, 2)
    qc.id(0)
    qc.measure_all()
    provider = QIProvider()
    backend = provider.get_backend(name=name)
    print(f"Running on backend: {backend.name}")
    qi_job = backend.run(qc)

    result = qi_job.result()
    assert result.success
    assert all(len(key) == num_qubits for key in result.get_counts())


def main(name: str) -> None:
    _run_e2e_tests(name=name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run E2E test on a backend.")
    parser.add_argument(
        "name",
        type=str,
        help="Name of the backend where the E2E tests will run.",
    )

    args = parser.parse_args()
    main(args.name)
