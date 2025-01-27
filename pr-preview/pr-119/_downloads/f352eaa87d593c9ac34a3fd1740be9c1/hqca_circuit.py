from typing import Any, Dict, List

from qiskit.circuit import QuantumCircuit

from qiskit_quantuminspire import cqasm
from qiskit_quantuminspire.hybrid.quantum_interface import QuantumInterface


def generate_circuit() -> str:
    # Create a basic Bell State circuit:
    qc = QuantumCircuit(2, 2)
    qc.reset(0)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    return cqasm.dumps(qc)


def execute(qi: QuantumInterface) -> None:
    """Run the classical part of the Hybrid Quantum/Classical Algorithm.

    Args:
        qi: A QuantumInterface instance that can be used to execute quantum circuits

    The qi object has a single method called execute_circuit, its interface is described below:

    qi.execute_circuit args:
        circuit: a string representation of a quantum circuit
        number_of_shots: how often to execute the circuit
        raw_data_enabled (default: False): report measurement per shot (if supported by backend type)

    qi.execute_circuit return value:
        The results of executing the quantum circuit, this is an object with the following attributes
            results: The results from iteration n-1.
            raw_data: Measurement per shot as a list of strings (or None if disabled).
            shots_requested: The number of shots requested by the user for the previous iteration.
            shots_done: The number of shots actually run.
    """
    for i in range(1, 5):
        circuit = generate_circuit()
        _ = qi.execute_circuit(circuit, 1024)
        # To include measurement results per shot (raw_data):
        # result = qi.execute_circuit(circuit, 1024,
        # raw_data_enabled=True) raw_data = result.raw_data.

        # Note that you can also use the QIHybridBackend to run QuantumCircuits directly, in which case the memory flag
        # is used to enable/disable raw data.:
        # backend = QIHybridBackend(qi)
        # results = backend.run(circuit, shots=50, memory=False).result()


def finalize(list_of_measurements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate the results from all iterations into one final result.

    Args:
        list_of_measurements: List of all results from the previous iterations.

    Returns:
        A free-form result, with a `property`: `value` structure. Value can
        be everything serializable.
    """
    return {"results": list_of_measurements}
