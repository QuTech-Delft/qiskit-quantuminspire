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
    "ccx": "toffoli",
}

# Uses lower case for keys to normalize inconsistent capitalization of backends
_OPENSQUIRREL_TO_QISKIT_MAPPING: dict[str, str] = {v.lower(): k for k, v in _QISKIT_TO_OPENSQUIRREL_MAPPING.items()}


def qiskit_to_opensquirrel(instruction: str) -> str:
    """Translate a Qiskit gate name to the equivalent opensquirrel gate name."""
    return _QISKIT_TO_OPENSQUIRREL_MAPPING[instruction.lower()]


def opensquirrel_to_qiskit(instruction: str) -> str:
    """Translate an opensquirrel gate name to the equivalent Qiskit gate name."""
    return _OPENSQUIRREL_TO_QISKIT_MAPPING[instruction.lower()]


def supported_opensquirrel_instructions() -> list[str]:
    """Return a list of all supported opensquirrel instructions."""
    return list(_QISKIT_TO_OPENSQUIRREL_MAPPING.values())


def supported_qiskit_instructions() -> list[str]:
    """Return a list of all supported Qiskit instructions."""
    return list(_QISKIT_TO_OPENSQUIRREL_MAPPING.keys())
