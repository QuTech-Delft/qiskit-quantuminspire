from qiskit.transpiler import CouplingMap


def is_coupling_map_complete(coupling_map: CouplingMap) -> bool:
    """A complete digraph is a digraph in which there is a directed edge from every vertex to every other vertex."""
    distance_matrix = coupling_map.distance_matrix

    assert distance_matrix is not None

    is_semicomplete = all(distance in [1, 0] for distance in distance_matrix.flatten())

    return is_semicomplete and coupling_map.is_symmetric
