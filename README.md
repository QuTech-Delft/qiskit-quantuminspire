# Qiskit Quantum Inspire Provider

[![License](https://img.shields.io/github/license/qutech-delft/qiskit-quantuminspire.svg?style=popout-square)](https://opensource.org/licenses/Apache-2.0)

**Qiskit** is an open-source SDK for working with quantum computers at the level of circuits, algorithms, and application modules.

This project contains a provider that allows access to **[Quantum Inspire]** quantum systems.

## API Access

For access to the Quantum Inspire 2 API you can use the QI2 CLI. Once installed (see [repository](https://github.com/QuTech-Delft/quantuminspire2) for installation instructions), simply run the shell command below to log in to the production environment.

```bash
qi login "https://api.qi2.quantum-inspire.com"
```

## Installation

You can install the Qiskit-QI plugin using pip:

```bash
pip install qiskit-quantuminspire
```

## Getting started

To instantiate the provider, make sure you are logged into QI2 as described above, then create a provider:

```python
from qiskit_quantuminspire.qi_provider import QIProvider

provider = QIProvider()
```

Once the provider has been instantiated, it may be used to access supported backends:

```python
# Show all current supported backends:
print(provider.backends())

# Get Quantum Inspire's simulator backend:
simulator_backend = provider.get_backend("QX emulator")
```

### Submitting a Circuit

Once a backend has been specified, it may be used to submit circuits.
For example, running a Bell State:

```python
from qiskit import QuantumCircuit

# Create a basic Bell State circuit:
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

# Show a representation of the quantum circuit:
print(qc)

# Run the circuit on Quantum Inspire's platform:
job = simulator_backend.run(qc)

# Print the results.
print(job.result().get_counts())
```

### Transpilation

Depending on the chosen backends, certain gates may not be supported. Qiskit is aware of the capabilities of each backend, and can transpile
circuits to use only supported gates:

```python
# Show supported gates
print(simulator_backend.target)

# Create circuit with a gate the backend doesn't support:
qc = QuantumCircuit(2, 2)
qc.sx(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])


# Transpile the circuit for the target backend:
qc_compiled = transpile(qc, simulator_backend)
print(qc_compiled)
```

## Running Tests

This package uses the [pytest](https://docs.pytest.org/en/stable/) test runner, and other packages
for mocking interfactions, reporting coverage, etc.
These can be installed with `poetry install`.

To use pytest directly, just run:

```bash
tox -e test
```

## License

[Apache License 2.0].

[quantum inspire]: https://www.quantum-inspire.com/
[apache license 2.0]: https://github.com/qiskit-partners/qiskit-ionq/blob/master/LICENSE.txt
