import logging
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from qiskit import QuantumCircuit

from qiskit_quantuminspire.qi_backend import QIBackend
from tests.helpers import create_backend_type


@pytest.mark.parametrize(
    "gateset, topology, nqubits, expected_instructions",
    [
        (
            ["x", "sdag", "prep_y", "measure_z"],
            [[0, 1], [1, 2], [2, 0]],
            3,
            [
                ("x", (0,)),
                ("sdg", (0,)),
                ("measure", (0,)),
                ("x", (1,)),
                ("sdg", (1,)),
                ("measure", (1,)),
                ("x", (2,)),
                ("sdg", (2,)),
                ("measure", (2,)),
            ],
        ),
        (
            # Gates in upper case
            ["CZ", "X"],
            [[0, 1], [1, 2], [2, 0], [1, 0], [1, 3]],
            4,
            [
                ("x", (0,)),
                ("x", (1,)),
                ("x", (2,)),
                ("x", (3,)),
                ("cz", (0, 1)),
                ("cz", (1, 0)),
                ("cz", (1, 3)),
                ("cz", (1, 2)),
                ("cz", (2, 0)),
            ],
        ),
        (
            # CouplingMap is complete
            ["toffoli", "X90"],
            [[1, 0], [0, 1], [1, 2], [2, 1], [2, 0], [0, 2]],
            3,
            [
                ("rx", None),
                ("ccx", None),
            ],
        ),
    ],
)
def test_qi_backend_construction_target(
    gateset: list[str],
    topology: list[list[int]],
    nqubits: int,
    expected_instructions: list[tuple[str, tuple[int, ...]]],
) -> None:
    # Arrange
    backend_type = create_backend_type(gateset=gateset, topology=topology, nqubits=nqubits)

    # Act
    qi_backend = QIBackend(backend_type=backend_type)

    # Assert
    target = qi_backend.target
    actual_instructions = [(instruction.name, qubits) for instruction, qubits in target.instructions]

    assert target.num_qubits == nqubits
    for instruction in expected_instructions:
        assert instruction in actual_instructions
    for instruction in actual_instructions:
        assert instruction in expected_instructions


def test_qi_backend_construction_max_shots() -> None:
    # Arrange
    backend_type = create_backend_type(max_number_of_shots=4096)

    # Act
    qi_backend = QIBackend(backend_type=backend_type)

    # Assert
    assert qi_backend.max_shots == 4096


def test_qi_backend_repr() -> None:
    # Arrange
    backend_type = create_backend_type(max_number_of_shots=4096)

    # Act
    qi_backend = QIBackend(backend_type=backend_type)

    # Assert
    assert qi_backend.name in repr(qi_backend)


def test_qi_backend_run(mocker: MockerFixture) -> None:
    # Arrange
    job = MagicMock()
    mocker.patch("qiskit_quantuminspire.qi_backend.QIJob", return_value=job)
    backend_type = create_backend_type(max_number_of_shots=4096)
    qi_backend = QIBackend(backend_type=backend_type)

    # Act
    qc = QuantumCircuit(2, 2)
    qi_backend.run(qc)

    # Assert
    job.submit.assert_called_once()


def test_qi_backend_run_updates_shots(mocker: MockerFixture) -> None:
    # Arrange
    job = MagicMock()
    mocker.patch("qiskit_quantuminspire.qi_backend.QIJob", return_value=job)
    backend_type = create_backend_type(max_number_of_shots=4096)
    qi_backend = QIBackend(backend_type=backend_type)

    # Act
    qc = QuantumCircuit(2, 2)
    qi_backend.run(qc, shots=1500)

    # Assert
    assert qi_backend.options.get("shots") == 1500


def test_qi_backend_run_unsupported_options(mocker: MockerFixture) -> None:
    # Arrange
    job = MagicMock()
    mocker.patch("qiskit_quantuminspire.qi_backend.QIJob", return_value=job)
    backend_type = create_backend_type(max_number_of_shots=4096)
    qi_backend = QIBackend(backend_type=backend_type)

    # Act & Assert
    qc = QuantumCircuit(2, 2)
    with pytest.raises(AttributeError):
        qi_backend.run(qc, unsupported_option=True)


def test_qi_backend_run_no_shot_memory_support(mocker: MockerFixture) -> None:
    # Arrange
    job = MagicMock()
    mocker.patch("qiskit_quantuminspire.qi_backend.QIJob", return_value=job)
    backend_type = create_backend_type(max_number_of_shots=4096)
    qi_backend = QIBackend(backend_type=backend_type)

    # Act & Assert
    qc = QuantumCircuit(2, 2)
    with pytest.raises(ValueError):
        qi_backend.run(qc, memory=True)


def test_qi_backend_run_supports_shot_memory(mocker: MockerFixture) -> None:
    # Arrange
    job = MagicMock()
    mocker.patch("qiskit_quantuminspire.qi_backend.QIJob", return_value=job)
    backend_type = create_backend_type(max_number_of_shots=4096)
    backend_type.supports_shot_memory = True
    qi_backend = QIBackend(backend_type=backend_type)

    # Act
    qc = QuantumCircuit(2, 2)
    qi_backend.run(qc, memory=True)

    # Assert
    job.submit.assert_called_once()


def test_qi_backend_run_option_bad_value(mocker: MockerFixture) -> None:
    # Arrange
    job = MagicMock()
    mocker.patch("qiskit_quantuminspire.qi_backend.QIJob", return_value=job)
    backend_type = create_backend_type(max_number_of_shots=4096)
    qi_backend = QIBackend(backend_type=backend_type)

    # Act & Assert
    qc = QuantumCircuit(2, 2)
    with pytest.raises(ValueError):
        qi_backend.run(qc, seed_simulator=1)


def test_qi_backend_construction_toffoli_gate_unsupported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    # Create backend type with a Toffoli gate and a non-complete topology
    backend_type = create_backend_type(
        name="spin", gateset=["toffoli", "x"], topology=[[0, 1], [1, 2], [2, 0], [1, 0], [1, 3]], nqubits=4
    )
    # Act
    with caplog.at_level(logging.WARNING):
        qi_backend = QIBackend(backend_type=backend_type)

    target = qi_backend.target
    actual_instructions = [(instruction.name, qubits) for instruction, qubits in target.instructions]

    # Assert
    assert any(
        "Native toffoli gate in backend spin not supported for non-complete topology" in record.message
        for record in caplog.records
    )
    # Target still gets created but without Toffoli gate
    assert actual_instructions == [("x", (0,)), ("x", (1,)), ("x", (2,)), ("x", (3,))]


def test_qi_backend_construction_unknown_gate_ignored(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    # Create backend type with an unknown gate
    backend_type = create_backend_type(
        name="spin", gateset=["unknown", "x"], topology=[[0, 1], [1, 2], [2, 0]], nqubits=3
    )
    # Act
    with caplog.at_level(logging.WARNING):
        qi_backend = QIBackend(backend_type=backend_type)

    target = qi_backend.target
    actual_instructions = [(instruction.name, qubits) for instruction, qubits in target.instructions]

    # Assert
    assert any(
        "Ignoring unknown native gate(s) {'unknown'} for backend spin" in record.message for record in caplog.records
    )
    # Target still gets created but without the unknown gate
    assert actual_instructions == [("x", (0,)), ("x", (1,)), ("x", (2,))]
