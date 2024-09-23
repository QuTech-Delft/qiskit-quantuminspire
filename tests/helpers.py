from compute_api_client import BackendStatus, BackendType


def create_backend_type(
    gateset: list[str] = [],
    topology: list[list[int]] = [],
    nqubits: int = 0,
    default_number_of_shots: int = 1024,
    max_number_of_shots: int = 2048,
    name: str = "qi_backend",
) -> BackendType:
    """Helper for creating a backendtype with only the fields you care about."""
    return BackendType(
        name=name,
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
        native_gateset=""
    )
