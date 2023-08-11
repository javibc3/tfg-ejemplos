# -*- coding: utf-8 -*-
# zato: ide-deploy=True

import math
import json
import numpy as np
from braket.circuits import Circuit, circuit
from braket.circuits.qubit_set import QubitSetInput
from braket.devices import Device

from zato.server.service import AWSQuantumService


class ShorAlgorithm(AWSQuantumService):

    name = 'quantum.shor-algorithm'
    runs = 100
    quantum_computer = 'arn:aws:braket:::device/quantum-simulator/amazon/sv1'
    key_name = 'key'

    def circuit(self):
        return shors_algorithm(self.request.payload['N'], self.request.payload['a'])
    
    def after_circuit_execution(self):
        out = {
            "measurement_counts": self.circuit_result.measurement_counts,
            "N": self.request.payload['N'],
            "a": self.request.payload['a']
        }
        self.logger.info(json.dumps(out))
        response = self.invoke('shor.shor-post-procesing', json.dumps(out))
        self.response.payload = response

@circuit.subroutine(register=True)
def inverse_qft_noswaps(qubits: QubitSetInput) -> Circuit:
    """
    Construct a circuit object corresponding to the inverse Quantum Fourier Transform (QFT)
    algorithm, applied to the argument qubits.  Does not use recursion to generate the circuit.

    Args:
        qubits (QubitSetInput): Qubits on which to apply the inverse Quantum Fourier Transform

    Returns:
        Circuit: Circuit object that implements the inverse Quantum Fourier Transform algorithm
    """
    # Instantiate circuit object
    qft_circuit = Circuit()

    # Fet number of qubits
    num_qubits = len(qubits)

    # First add SWAP gates to reverse the order of the qubits:
    # for i in range(math.floor(num_qubits / 2)):
    #     qft_circuit.swap(qubits[i], qubits[-i - 1])

    # Start on the last qubit and work to the first.
    for k in reversed(range(num_qubits)):
        # Apply the controlled rotations, with weights (angles) defined by the distance to the
        # control qubit. These angles are the negative of the angle used in the QFT.
        # Start on the last qubit and iterate until the qubit after k.
        # When num_qubits==1, this loop does not run.
        for j in reversed(range(1, num_qubits - k)):
            angle = -2 * math.pi / (2 ** (j + 1))
            qft_circuit.cphaseshift(qubits[k + j], qubits[k], angle)

        # Then add a Hadamard gate
        qft_circuit.h(qubits[k])

    return qft_circuit

@circuit.subroutine(register=True)
def modular_exponentiation_amod15(
    counting_qubits: QubitSetInput, aux_qubits: QubitSetInput, integer_a: int
) -> Circuit:
    """
    Construct a circuit object corresponding the modular exponentiation of a^x Mod 15

    Args:
        counting_qubits (QubitSetInput): Qubits defining the counting register
        aux_qubits (QubitSetInput) : Qubits defining the auxilary register
        integer_a (int) : Any integer that satisfies 1 < a < N and gcd(a, N) = 1.
    Returns:
        Circuit: Circuit object that implements the modular exponentiation of a^x Mod 15
    """

    # Instantiate circuit object
    mod_exp_amod15 = Circuit()

    for x in counting_qubits:
        r = 2**x
        if integer_a not in [2, 7, 8, 11, 13]:
            raise ValueError("integer 'a' must be 2,7,8,11 or 13")
        for iteration in range(r):
            if integer_a in [2, 13]:
                mod_exp_amod15.cswap(x, aux_qubits[0], aux_qubits[1])
                mod_exp_amod15.cswap(x, aux_qubits[1], aux_qubits[2])
                mod_exp_amod15.cswap(x, aux_qubits[2], aux_qubits[3])
            if integer_a in [7, 8]:
                mod_exp_amod15.cswap(x, aux_qubits[2], aux_qubits[3])
                mod_exp_amod15.cswap(x, aux_qubits[1], aux_qubits[2])
                mod_exp_amod15.cswap(x, aux_qubits[0], aux_qubits[1])
            if integer_a == 11:
                mod_exp_amod15.cswap(x, aux_qubits[1], aux_qubits[3])
                mod_exp_amod15.cswap(x, aux_qubits[0], aux_qubits[2])
            if integer_a in [7, 11, 13]:
                for q in aux_qubits:
                    mod_exp_amod15.cnot(x, q)

    return mod_exp_amod15

@circuit.subroutine(register=True) 
def shors_algorithm(integer_N: int, integer_a: int) -> Circuit:
    """
    Creates the circuit for Shor's algorithm.
    1) Based on integer N, calculate number of counting qubits for the first register
    2) Setup same number of auxiliary qubits for the second register
        and apply modular exponentian function
    3) Apply inverse_QFT

    Args:
        integer_N (int) : The integer N to be factored
        integer_a (int) : Any integer 'a' that satisfies 1 < a < N and gcd(a, N) = 1.

    Returns:
        Circuit: Circuit object that implements the Shor's algorithm
    """

    # validate the inputs
    if integer_N < 1 or integer_N % 2 == 0:
        raise ValueError("The input N needs to be an odd integer greater than 1.")
    if integer_a >= integer_N or math.gcd(integer_a, integer_N) != 1:
        raise ValueError('The integer "a" needs to satisfy 1 < a < N and gcd(a, N) = 1.')

    # calculate number of qubits needed
    n = int(np.ceil(np.log2(integer_N)))
    m = n

    counting_qubits = [*range(n)]
    aux_qubits = [*range(n, n + m)]

    shors_circuit = Circuit()

    # Initialize counting and aux qubits
    shors_circuit.h(counting_qubits)
    shors_circuit.x(aux_qubits[0])

    # Apply modular exponentiation
    shors_circuit.modular_exponentiation_amod15(counting_qubits, aux_qubits, integer_a)

    # Apply inverse QFT
    shors_circuit.inverse_qft_noswaps(counting_qubits)

    return shors_circuit

