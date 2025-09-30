from typing import Any, Callable, Dict, Generator, Optional, Type
from unittest.mock import MagicMock, PropertyMock

import pytest
from compute_api_client import BackendStatus
from pytest_mock import MockerFixture
from qiskit import QuantumCircuit

from qiskit_quantuminspire.mapping.instruction_mapping import InstructionMapping
from qiskit_quantuminspire.qi_backend import QIBackend
from tests.helpers import create_backend_type


@pytest.fixture()
def qi_job_mock(mocker: MockerFixture) -> Generator[MagicMock, None, None]:
    job = MagicMock()
    job.submit = MagicMock()
    mocker.patch("qiskit_quantuminspire.qi_backend.QIJob", return_value=job)
    yield job
    job.submit.reset_mock()


@pytest.fixture
def qi_backend_factory(mocker: MockerFixture) -> Callable[..., QIBackend]:
    def _generate_qi_backend(params: Optional[Dict[Any, Any]] = None) -> QIBackend:
        params = params or {}
        backend_type = params.pop(
            "backend_type", create_backend_type(max_number_of_shots=4096, supports_raw_data=False)
        )
        is_online = params.pop("backend_online", True)
        status = BackendStatus.IDLE if is_online else BackendStatus.OFFLINE

        qi_backend = QIBackend(backend_type=backend_type)
        mocker.patch.object(type(qi_backend), "status", PropertyMock(return_value=status))  # The class of the instance

        return qi_backend

    return _generate_qi_backend


# Exclude the "barrier" instruction as it is not part of the target, but include asm instruction which leaves the
# number of instructions unchanged
NUM_SUPPORTED_INSTRUCTIONS = len(InstructionMapping().supported_opensquirrel_instructions())


@pytest.mark.parametrize(
    "gateset, topology, nqubits, expected_instructions, mapping",
    [
        (
            ["x", "sdag", "prep_y", "measure"],
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
                ("asm", ()),
            ],
            InstructionMapping(qiskit_to_os={"sdg": "sDaG", "x": "X", "prep_y": "prep_y", "measure": "measure"}),
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
                ("asm", ()),
            ],
            InstructionMapping(qiskit_to_os={"cz": "CZ", "x": "X"}),
        ),
        (
            # CouplingMap is complete
            ["toffoli", "rx"],
            [[1, 0], [0, 1], [1, 2], [2, 1], [2, 0], [0, 2]],
            3,
            [
                ("rx", None),
                ("ccx", None),
                ("asm", ()),
            ],
            InstructionMapping(qiskit_to_os={"ccx": "toffoli", "rx": "rx"}),
        ),
    ],
)
def test_qi_backend_construction_target(
    gateset: list[str],
    topology: list[list[int]],
    nqubits: int,
    expected_instructions: list[tuple[str, tuple[int, ...]]],
    mapping: InstructionMapping,
) -> None:
    # Arrange
    backend_type = create_backend_type(gateset=gateset, topology=topology, nqubits=nqubits)

    # Act
    qi_backend = QIBackend(backend_type=backend_type, mapping=mapping)

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


@pytest.mark.parametrize("backend_online", [True, False])  # Test cases for backend being available and offline
def test_qi_backend_run_backend_status(
    qi_job_mock: MagicMock, qi_backend_factory: Callable[..., QIBackend], backend_online: bool
) -> None:
    # Arrange
    qi_backend = qi_backend_factory(params={"backend_online": backend_online})
    qc = QuantumCircuit(2, 2)

    # Act & Assert
    if backend_online:
        qi_backend.run(qc)
        qi_job_mock.submit.assert_called_once()
    else:
        with pytest.raises(RuntimeError):
            qi_backend.run(qc)


def test_qi_backend_run_updates_shots(qi_job_mock: MagicMock, qi_backend_factory: Callable[..., QIBackend]) -> None:
    # Arrange
    qi_backend = qi_backend_factory()

    # Act
    qc = QuantumCircuit(2, 2)
    qi_backend.run(qc, shots=1500)

    # Assert
    assert qi_backend.options.get("shots") == 1500


@pytest.mark.parametrize(
    "option, value, expected_exception",
    [
        ("unsupported_option", True, AttributeError),
        ("memory", True, ValueError),
        ("seed_simulator", 1, ValueError),
    ],
)
def test_qi_backend_run_with_unsupported_options(
    qi_job_mock: MagicMock,
    qi_backend_factory: Callable[..., QIBackend],
    option: str,
    value: Any,
    expected_exception: Type[Exception],
) -> None:
    # Arrange
    qi_backend = qi_backend_factory()

    # Act & Assert
    qc = QuantumCircuit(2, 2)
    with pytest.raises(expected_exception):
        qi_backend.run(qc, **{option: value})


def test_qi_backend_run_supports_shot_memory(
    qi_job_mock: MagicMock, qi_backend_factory: Callable[..., QIBackend]
) -> None:
    # Arrange
    backend_type = create_backend_type(max_number_of_shots=4096)
    backend_type.supports_raw_data = True
    qi_backend = qi_backend_factory(params={"backend_type": backend_type})

    # Act
    qc = QuantumCircuit(2, 2)
    qi_backend.run(qc, memory=True)

    # Assert
    qi_job_mock.submit.assert_called_once()


def test_qi_backend_construction_toffoli_gate_unsupported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    # Create backend type with a Toffoli gate and a non-complete topology
    nqubits = 4
    backend_type = create_backend_type(
        name="spin", gateset=["toffoli", "x"], topology=[[0, 1], [1, 2], [2, 0], [1, 0], [1, 3]], nqubits=nqubits
    )

    # Act
    qi_backend = QIBackend(backend_type=backend_type)

    target = qi_backend.target
    instructions: list[str] = [instruction.name for instruction, _ in target.instructions]

    # Assert
    assert "ccx" not in instructions
    # Target still gets created but without the toffoli gate
    assert len(instructions) == 81


def test_qi_backend_construction_unknown_gate_ignored(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    # Create backend type with an unknown gate
    nqubits = 3
    backend_type = create_backend_type(
        name="spin",
        gateset=["unknown", "x"],
        topology=[[1, 0], [0, 1], [1, 2], [2, 1], [2, 0], [0, 2]],
        nqubits=nqubits,
    )

    # Act
    qi_backend = QIBackend(backend_type=backend_type)

    target = qi_backend.target
    instructions: list[str] = [instruction.name for instruction, _ in target.instructions]

    # Assert
    # Target still gets created but without the unknown gate
    assert len(instructions) == NUM_SUPPORTED_INSTRUCTIONS
