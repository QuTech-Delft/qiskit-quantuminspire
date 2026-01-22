from datetime import datetime, timezone
from typing import Optional

from compute_api_client import BackendStatus, BackendType, Result as RawJobResult


def create_backend_type(
    gateset: list[str] = [],
    topology: list[list[int]] = [[0, 1], [1, 0]],
    nqubits: int = 2,
    default_number_of_shots: int = 1024,
    max_number_of_shots: int = 2048,
    name: str = "qi_backend",
    id: int = 1,
    supports_raw_data: bool = True,
) -> BackendType:
    """Helper for creating a backendtype with only the fields you care about."""
    return BackendType(
        name=name,
        nqubits=nqubits,
        gateset=gateset,
        topology=topology,
        id=id,
        is_hardware=True,
        image_id="qi_backend",
        features=[],
        default_compiler_config={},
        status=BackendStatus.IDLE,
        default_number_of_shots=default_number_of_shots,
        max_number_of_shots=max_number_of_shots,
        infrastructure="QCI",
        description="A Quantum Inspire backend",
        native_gateset="",
        supports_raw_data=supports_raw_data,
        enabled=True,
        messages={"backend": {"content": "message for backend"}},
        job_execution_time_limit=3600,
        identifier="dummy",
    )


def create_raw_job_result(
    results: dict[str, int] = {
        "0000000000": 256,
        "0000000001": 256,
        "0000000010": 256,
        "0000000011": 256,
    },
    raw_data: Optional[list[str]] = None,
) -> RawJobResult:
    return RawJobResult(
        id=1,
        metadata_id=1,
        created_on=datetime(2022, 10, 25, 15, 37, 54, 269823, tzinfo=timezone.utc),
        execution_time_in_seconds=1.23,
        shots_requested=100,
        shots_done=100,
        results=results,
        raw_data=raw_data,
        job_id=10,
    )
