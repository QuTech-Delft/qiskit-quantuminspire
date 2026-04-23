# Basics

Quantum Inspire supports hybrid classical-quantum algorithms, and allows execution of both the quantum and the classical part fully on the QI servers.

## Script format

Any script that will be executed on the Quantum Inspire platform is required to have at least the `execute()` and `finalize()` functions.

### Execute

The execute function is the function that gets called by QI first. As an argument it gets a `QuantumInterface`, which is what allows you to actually execute your circuit. A simple example, where a function `generate_circuit()` is called that returns cQASM as a string, is shown below. In this example, the same circuit is executed 5 times in a row as a simple illustration of the interchanging control between the hybrid and classical domains. Normally, you might want to change your `QuantumCircuit` between each execution based on your results.

```python
def execute(qi: QuantumInterface) -> None:
    """Run the classical part of the Hybrid Quantum/Classical Algorithm.

    Args:
        qi: A QuantumInterface instance that can be used to execute quantum circuits

    The qi object has a single method called execute_circuit, its interface is described below:

    qi.execute_circuit args:
        circuit: a string representation of a quantum circuit
        number_of_shots: how often to execute the circuit
        raw_data_enabled (default: False): report measurement per shot (if supported by backend type)

    qi.execute_circuit return value:
        The results of executing the quantum circuit, this is an object with the following attributes
            results: The results from iteration n-1.
            raw_data: Measurement per shot as a list of strings (or None if disabled).
            shots_requested: The number of shots requested by the user for the previous iteration.
            shots_done: The number of shots actually run.
    """
    for i in range(1, 5):
        circuit = generate_circuit()
        _ = qi.execute_circuit(circuit, 1024)
```

Refer to [this example](./hqca_circuit.py) for some extra ways to interact with the `QuantumInterface`.

### Finalize

The `finalize()` function allows you to aggregate your results. It should return a dictionary which will be stored as the final result. By default it takes a list of all measurements as an argument, but through the use of globals you could also export other data.

```python
def finalize(list_of_measurements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate the results from all iterations into one final result.

    Args:
        list_of_measurements: List of all results from the previous iterations.

    Returns:
        A free-form result, with a `property`: `value` structure. Value can
        be everything serializable.
    """
    return {"results": list_of_measurements}
```

## Execution

A complete script with both example functions can be found [here](./hqca_circuit.py). This can be uploaded to QI as follows (using the CLI), where `<backend_id>` is the id number of the selected quantum backend, which can be retrieved using the Qiskit-QuantumInspire QIProvider.

```bash
qi files upload ./hqca_circuit.py <backend_id>
```

The final results can be retrieved as follows, where `<job_id>` is the job id returned by the previous command.

```bash
qi final_results get <job_id>
```
