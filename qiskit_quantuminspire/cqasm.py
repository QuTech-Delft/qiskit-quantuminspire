from opensquirrel import CircuitBuilder
from opensquirrel.ir import Bit, Float, Qubit
from opensquirrel.writer import writer
from qiskit import QuantumCircuit

_QISKIT_TO_OPENSQUIRREL_MAPPING: dict[str, str] = {
    "id": "I",
    "h": "H",
    "x": "X",
    "y": "Y",
    "z": "Z",
    "s": "S",
    "sdg": "Sdag",
    "t": "T",
    "tdg": "Tdag",
    "rx": "Rx",
    "ry": "Ry",
    "rz": "Rz",
    "cx": "CNOT",
    "cz": "CZ",
    "cp": "CR",
    "swap": "SWAP",
    "measure": "measure",
    "reset": "reset",
}


def dumps(circuit: QuantumCircuit) -> str:
    """Return the cQASM representation of the circuit."""
    builder = CircuitBuilder(circuit.num_qubits, circuit.num_clbits)
    for circuit_instruction in circuit.data:
        operation = circuit_instruction.operation
        name = operation.name
        params = [Float(param) for param in operation.params]
        qubit_operands = [Qubit(qubit._index) for qubit in circuit_instruction.qubits]
        clbit_operands = [Bit(clbit._index) for clbit in circuit_instruction.clbits]

        if name == "barrier":
            continue  # Should be ignored?

        getattr(builder, _QISKIT_TO_OPENSQUIRREL_MAPPING[name])(*qubit_operands, *clbit_operands, *params)

    return writer.circuit_to_string(builder.to_circuit())
