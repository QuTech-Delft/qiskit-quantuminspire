from typing import List, Self

from compute_api_client import BackendType
from pydantic import BaseModel


class BackendMetadata(BaseModel):
    name: str
    description: str
    id: int
    max_number_of_shots: int
    default_number_of_shots: int
    supports_raw_data: bool
    gateset: List[str]
    topology: List[List[int]]
    nqubits: int

    @classmethod
    def from_backend_type(cls, backend_type: BackendType) -> Self:
        return cls(
            name=backend_type.name,
            description=backend_type.description,
            id=backend_type.id,
            max_number_of_shots=backend_type.max_number_of_shots,
            default_number_of_shots=backend_type.default_number_of_shots,
            supports_raw_data=backend_type.supports_raw_data,
            gateset=backend_type.gateset,
            topology=backend_type.topology,
            nqubits=backend_type.nqubits,
        )
