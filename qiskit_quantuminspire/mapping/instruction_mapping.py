_DEFAULT_QISKIT_TO_OPENSQUIRREL_MAPPING: dict[str, str] = {
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
    "ccx": "toffoli",
}


class InstructionMapping:
    def __init__(self, qiskit_to_os: dict[str, str] = _DEFAULT_QISKIT_TO_OPENSQUIRREL_MAPPING):
        self._QISKIT_TO_OPENSQUIRREL_MAPPING: dict[str, str] = qiskit_to_os
        # Uses lower case for keys to normalize inconsistent capitalization of backends
        self._OPENSQUIRREL_TO_QISKIT_MAPPING: dict[str, str] = {
            v.lower(): k for k, v in self._QISKIT_TO_OPENSQUIRREL_MAPPING.items()
        }

    def qiskit_to_opensquirrel(self, instruction: str) -> str:
        """Translate a Qiskit gate name to the equivalent opensquirrel gate name."""
        return self._QISKIT_TO_OPENSQUIRREL_MAPPING[instruction.lower()]

    def opensquirrel_to_qiskit(self, instruction: str) -> str:
        """Translate an opensquirrel gate name to the equivalent Qiskit gate name."""
        return self._OPENSQUIRREL_TO_QISKIT_MAPPING[instruction.lower()]

    def supported_opensquirrel_instructions(self) -> list[str]:
        """Return a list of all supported opensquirrel instructions."""
        return list(self._QISKIT_TO_OPENSQUIRREL_MAPPING.values())

    def supported_qiskit_instructions(self) -> list[str]:
        """Return a list of all supported Qiskit instructions."""
        return list(self._QISKIT_TO_OPENSQUIRREL_MAPPING.keys())
