# Qiskit Quantum Inspire Provider

[![License](https://img.shields.io/github/license/qutech-delft/qiskit-quantuminspire.svg?style=popout-square)](https://opensource.org/licenses/Apache-2.0)

**Qiskit** is an open-source SDK for working with quantum computers at the level of circuits, algorithms, and application modules.

This project contains a provider that allows access to **[Quantum Inspire]** quantum systems.

## API Access

...

## Installation

You can install the provider using pip:

```bash
pip install qiskit-quantuminspire
```

## Provider Setup

To instantiate the provider, make sure you have an access token then create a provider:

```python
from qiskit_quantuminspire import QIProvider

provider = QIProvider()
```

Once the provider has been instantiated, it may be used to access supported backends:

```python
# Show all current supported backends:
print(provider.backends())

# Get Quantum Inspire's simulator backend:
simulator_backend = provider.get_backend("qx_emulator")
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

# Run the circuit on Quantum Inspire's platform:
job = simulator_backend.run(qc)

# Print the results.
print(job.result().get_counts())

# Get results with a different aggregation method when debiasing
# is applied as an error mitigation strategy
print(job.result(sharpen=True).get_counts())

# The simulator specifically provides the the ideal probabilities and creates
# counts by sampling from these probabilities. The raw probabilities are also accessible:
print(job.result().get_probabilities())
```

## Contributing

...

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
