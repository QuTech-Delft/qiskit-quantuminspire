import asyncio
import concurrent
from typing import Any, Coroutine

from qiskit.transpiler import CouplingMap


def is_coupling_map_complete(coupling_map: CouplingMap) -> bool:
    """A complete digraph is a digraph in which there is a directed edge from every vertex to every other vertex."""
    distance_matrix = coupling_map.distance_matrix

    assert distance_matrix is not None

    is_semicomplete = all(distance in [1, 0] for distance in distance_matrix.flatten())

    return is_semicomplete and coupling_map.is_symmetric


def run_async(async_function: Coroutine[Any, Any, Any]) -> Any:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, async_function)
            return future.result()
    else:
        return asyncio.run(async_function)
