# How to: Submit a circuit

## Getting a backend

To instantiate the provider, make sure you are logged into QI2, then create a provider:

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

## Submitting a Circuit

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

## Transpilation

Depending on the chosen backends, certain gates may not be supported. Qiskit is aware of the capabilities of each backend, and can transpile
circuits to use only supported gates:

```python
from qiskit import transpile

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