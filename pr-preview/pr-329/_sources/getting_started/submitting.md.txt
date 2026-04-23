# How to: Submit a circuit

## Getting a backend

To instantiate the provider, make sure you are logged into Quantum Inspire, then create a provider:

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
result = job.result()
print(result.get_counts())
```

When submitting circuits, some may fail during execution. To get details about these errors, check the `system_messages` attribute of the result object.

```python
# Get the error messages corresponding to each failed circuit
print(result.system_messages)
```

The attribute returns a dictionary where:

- **Keys**: Circuit names
- **Values**: Dictionaries containing:
  - **`message`**: The error message from the system
  - **`trace_id`**: A unique identifier for debugging

### Debugging with `trace_id`

If you need support from Quantum Inspire, you can provide the `trace_id` to assist with troubleshooting.



On backends that support the `raw data` feature, you can set the `memory` option to get the measurement result of each individual shot:

```python
job = simulator_backend.run(qc, memory=True)
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

## Support for Assembly declaration

The qiskit-quantuminspire plugin also supports assembly declarations that can be used to add backend-specific (assembly) code to a qiskit circuit. 
They are realized through an `Asm` instruction. 

```python
from qiskit import QuantumCircuit

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.append(Asm(backend_name="TestBackend", asm_code=""" a ' " {} () [] b """))
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])
```

The corresponding `cQASM` that gets generated for this circuit looks like 

```
version 3.0

qubit[2] q
bit[2] b

H q[0]
asm(TestBackend) ''' a ' " {} () [] b '''
CNOT q[0], q[1]
b[0] = measure q[0]
b[1] = measure q[1]
```
See [Assembly declaration](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/assembly_declaration.html) for asm instructions.