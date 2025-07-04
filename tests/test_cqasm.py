import math

import pytest
from qiskit import QuantumCircuit

from qiskit_quantuminspire.cqasm import dumps
from qiskit_quantuminspire.qi_instructions import Asm


def test_cqasm_dumps() -> None:
    # Arrange
    qc = QuantumCircuit(3)
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
    qc.reset(2)
    qc.cz(1, 2)
    qc.cp(math.pi / 2, 1, 2)
    qc.id(0)
    qc.measure_all()

    expected_cqasm = """version 3.0

qubit[3] q
bit[3] b

H q[0]
asm(TestBackend) ''' a ' " {} () [] b '''
X q[1]
Y q[2]
CNOT q[0], q[1]
Z q[1]
S q[0]
Rx(1.5707963) q[0]
Ry(1.5707963) q[1]
Rz(1.5707963) q[2]
Sdag q[2]
T q[1]
Tdag q[0]
reset q[2]
CZ q[1], q[2]
CR(1.5707963) q[1], q[2]
I q[0]
barrier q[0]
barrier q[1]
barrier q[2]
b[0] = measure q[0]
b[1] = measure q[1]
b[2] = measure q[2]
"""
    # Act
    serialized_cqasm = dumps(qc)

    # Assert
    assert serialized_cqasm == expected_cqasm


def test_cqasm_unsupported_instruction() -> None:
    # Arrange
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.x(1)
    qc.rzx(math.pi / 2, 0, 1)  # Unsupported instruction

    # Act
    with pytest.raises(NotImplementedError):
        dumps(qc)


def test_cqasm_unsupported_delay_unit() -> None:
    # Arrange
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.delay(20, unit="ns")  # Unsupported delay unit
    qc.x(1)

    # Act
    with pytest.raises(NotImplementedError):
        dumps(qc)


def test_cqasm_without_unit() -> None:
    # Arrange
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.delay(20)
    qc.x(1)

    # Act
    cqasm = dumps(qc)

    # Assert
    assert "wait(20)" in cqasm
