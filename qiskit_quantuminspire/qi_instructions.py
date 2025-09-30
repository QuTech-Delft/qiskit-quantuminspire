from qiskit.circuit import Instruction


class Asm(Instruction):  # type: ignore[misc]
    # Mark as directive like Barrier,
    # see https://docs.quantum.ibm.com/api/qiskit/circuit_library#standard-directives
    _directive = True
    NAME = "asm"

    def __init__(self, backend_name: str = "", asm_code: str = ""):
        super().__init__(self.NAME, 0, 0, [backend_name, asm_code])
