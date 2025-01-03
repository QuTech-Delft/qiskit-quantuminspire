import asyncio

import pytest
from qiskit.transpiler import CouplingMap

from qiskit_quantuminspire.utils import is_coupling_map_complete, run_async


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


def test_async_run_no_loop() -> None:
    async def t_coro() -> None:
        await asyncio.sleep(1)

    run_async(t_coro())


def test_async_run_loop() -> None:
    async def t_coro() -> None:
        await asyncio.sleep(1)

    async def main() -> None:
        run_async(t_coro())

    asyncio.run(main())
