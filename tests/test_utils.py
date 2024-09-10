import pytest
from qiskit.transpiler import CouplingMap

from qiskit_quantuminspire.utils import is_coupling_map_complete


@pytest.mark.parametrize(
    "coupling_map, is_complete",
    [
        (CouplingMap([[0, 1], [1, 2], [2, 0]]), False),  # semicomplete, not symmetric
        (CouplingMap.from_full(10), True),
        (CouplingMap([[1, 0], [0, 1], [1, 2], [2, 1], [2, 0], [0, 2]]), True),
        (CouplingMap([[0, 1], [1, 0], [2, 3], [3, 2]]), False),  # symmetric, but unconnected
        (
            CouplingMap([[0, 1], [1, 0], [1, 2], [2, 1], [2, 3], [3, 2]]),
            False,
        ),  # symmetric, connected, but not semicomplete
    ],
)
def test_is_coupling_map_complete(coupling_map: CouplingMap, is_complete: bool) -> None:
    assert is_coupling_map_complete(coupling_map) == is_complete
