# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from braket.circuits.circuit import Circuit

import numpy as np
from braket.circuits import Circuit

from zato.server.service import AWSQuantumService

class QuantumWalk(AWSQuantumService):

    name = 'quantum.quantum-walk'
    runs = 1000
    quantum_computer = 'arn:aws:braket:::device/quantum-simulator/amazon/sv1'
    key_name = 'key'

    def circuit(self) -> Circuit:
        return quantum_walk(4)

    def after_circuit_execution(self):

        # get measurement results
        measurement_counts = self.circuit_result.measurement_counts

        quantum_walk_measurement_counts = {}
        for key, val in self.circuit_result.measurement_counts.items():
            node = int(key[1:][::-1], 2)
            if node in quantum_walk_measurement_counts:
                quantum_walk_measurement_counts[node] += val / self.get_runs()
            else:
                quantum_walk_measurement_counts[node] = val / self.get_runs()

        output = {
            "task_metadata": self.circuit_result.task_metadata,
            "measurements": self.circuit_result.measurements,
            "measured_qubits": self.circuit_result.measured_qubits,
            "measurement_counts": measurement_counts,
            "measurement_probabilities": self.circuit_result.measurement_probabilities,
            "quantum_walk_measurement_counts": quantum_walk_measurement_counts,
        }
        self.response.payload = str(output)
        


def qft(num_qubits: int, inverse: bool = False) -> Circuit:
    """Creates the quantum Fourier transform circuit and its inverse.

    Args:
        num_qubits (int): Number of qubits in the circuit
        inverse (bool): If true return the inverse of the circuit. Default is False

    Returns:
        Circuit: Circuit object that implements the quantum Fourier transform or its inverse
    """

    qc = Circuit()
    N = num_qubits - 1

    if not inverse:
        qc.h(N)
        for n in range(1, N + 1):
            qc.cphaseshift(N - n, N, 2 * np.pi / 2 ** (n + 1))

        for i in range(1, N):
            qc.h(N - i)
            for n in range(1, N - i + 1):
                qc.cphaseshift(N - (n + i), N - i, 2 * np.pi / 2 ** (n + 1))
        qc.h(0)

    else:  # The inverse of the quantum Fourier transform
        qc.h(0)
        for i in range(N - 1, 0, -1):
            for n in range(N - i, 0, -1):
                qc.cphaseshift(N - (n + i), N - i, -2 * np.pi / 2 ** (n + 1))
            qc.h(N - i)

        for n in range(N, 0, -1):
            qc.cphaseshift(N - n, N, -2 * np.pi / 2 ** (n + 1))

        qc.h(N)

    return qc


def qft_conditional_add_1(num_qubits: int) -> Circuit:
    """Creates the quantum circuit that conditionally add +1 or -1 using:

    1) The first qubit to control if add 1 or subtract 1: when the first qubit is 0, we add 1 from
    the number, and when the first qubit is 1, we subtract 1 from the number.

    2) The second register with `num_qubits` qubits to save the result.

    Args:
        num_qubits (int): Number of qubits that saves the result.

    Returns:
        Circuit: Circuit object that implements the circuit that conditionally add +1 or -1.
    """

    qc = Circuit()
    qc.add(qft(num_qubits), target=range(1, num_qubits + 1))

    # add \pm 1 with control phase gates
    for i in range(num_qubits):
        qc.cphaseshift01(control=0, target=num_qubits - i, angle=2 * np.pi / 2 ** (num_qubits - i))
        qc.cphaseshift(control=0, target=num_qubits - i, angle=-2 * np.pi / 2 ** (num_qubits - i))

    qc.add(qft(num_qubits, inverse=True), target=range(1, num_qubits + 1))

    return qc


def quantum_walk(n_nodes: int, num_steps: int = 1) -> Circuit:
    """Creates the quantum random walk circuit.

    Args:
        n_nodes (int): The number of nodes in the graph
        num_steps (int): The number of steps for the quantum walk. Default is 1

    Returns:
        Circuit: Circuit object that implements the quantum random walk algorithm

    Raises:
        If `np.log2(n_nodes)` is not an integer, a value error will be raised.
    """

    n = np.log2(n_nodes)  # number of qubits for the graph

    if float(n).is_integer():
        n = int(n)
    else:
        raise ValueError("The number of nodes has to be 2^n for integer n.")

    qc = Circuit()
    for _ in range(num_steps):
        qc.h(0)
        qc.add_circuit(qft_conditional_add_1(n))
        qc.x(0)  # flip the coin after the shift

    return qc