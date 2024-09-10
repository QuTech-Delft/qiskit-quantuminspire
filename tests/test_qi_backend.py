import pytest
from compute_api_client import BackendStatus, BackendType

from qiskit_quantuminspire.qi_backend import QIBackend


def create_backend_type(
    gateset: list[str] = [],
    topology: list[list[int]] = [],
    nqubits: int = 0,
    default_number_of_shots: int = 1024,
    max_number_of_shots: int = 2048,
) -> BackendType:
    """Helper for creating a backendtype with only the fields you care about."""
    return BackendType(
        name="qi_backend",
        nqubits=nqubits,
        gateset=gateset,
        topology=topology,
        id=1,
        is_hardware=True,
        image_id="qi_backend",
        features=[],
        default_compiler_config="",
        status=BackendStatus.IDLE,
        default_number_of_shots=default_number_of_shots,
        max_number_of_shots=max_number_of_shots,
        infrastructure="QCI",
        description="A Quantum Inspire backend",
    )


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
            ["cz", "x"],
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
    target = qi_backend.target()
    actual_instructions = [(instruction.name, qubits) for instruction, qubits in target.instructions]
    print(target.instructions)

    assert target.num_qubits == nqubits
    for instruction in expected_instructions:
        assert instruction in actual_instructions
    for instruction in actual_instructions:
        assert instruction in expected_instructions
