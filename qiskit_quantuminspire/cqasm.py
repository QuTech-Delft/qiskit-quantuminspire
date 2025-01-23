from typing import Any

from opensquirrel import CircuitBuilder
from opensquirrel.ir import Bit, Qubit
from opensquirrel.writer import writer
from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction

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
    "barrier": "barrier",
    "delay": "wait",
}


def _add_instruction(builder: CircuitBuilder, circuit_instruction: Any) -> None:
    operation = circuit_instruction.operation
    name = operation.name
    params = [param for param in operation.params]
    qubit_operands = [Qubit(qubit._index) for qubit in circuit_instruction.qubits]
    clbit_operands = [Bit(clbit._index) for clbit in circuit_instruction.clbits]

    try:
        # Get the gate's method in the CircuitBuilder class, call with operands
        # All of the builder's methods follow the same pattern, first the qubit operands, then parameters
        # Only method with classical bit operands is measure, which does not have parameters
        getattr(builder, _QISKIT_TO_OPENSQUIRREL_MAPPING[name])(*qubit_operands, *clbit_operands, *params)
    except KeyError:
        raise NotImplementedError(
            f"Unsupported instruction: {name}. Please edit your circuit or use Qiskit transpilation to support "
            + "your selected backend."
        )


def dumps(circuit: QuantumCircuit) -> str:
    """Return the cQASM representation of the circuit."""
    builder = CircuitBuilder(circuit.num_qubits, circuit.num_clbits)
    for circuit_instruction in circuit.data:
        operation = circuit_instruction.operation
        name = operation.name

        if name == "delay":
            if circuit_instruction.unit != "dt":
                raise NotImplementedError(
                    f"Unsupported delay unit {circuit_instruction.unit} in: {circuit_instruction}. Only 'dt'"
                    + " is supported."
                )

        if name == "barrier":
            # Opensquirrel does not support multi-qubit barriers.
            for qubit in circuit_instruction.qubits:
                _add_instruction(builder, CircuitInstruction(operation=operation, qubits=[qubit]))
            continue

        _add_instruction(builder, circuit_instruction)

    cqasm: str = writer.circuit_to_string(builder.to_circuit())

    return cqasm
