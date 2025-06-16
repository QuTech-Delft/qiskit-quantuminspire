from qiskit.circuit import Instruction


class Asm(Instruction):
    def __init__(self, backend_name: str, asm_code: str):
        name = "asm"
        num_qubits = 0
        num_clbits = 0
        params = [backend_name, asm_code]
        super().__init__(name, num_qubits, num_clbits, params)
