# -*- coding: utf-8 -*-
# zato: ide-deploy=True

import json
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

# Zato
from zato.server.service import IBMQuantumService

# ##############################################################################

class QuantumRandomNumberGeneratosService(IBMQuantumService):
    """ Generates quantum random numbers
    """
    name = 'quantum.qrng'
    quantum_computer = 'ibmq_qasm_simulator'
    key_name = 'ibm_quantum'

    def circuit(self):

        qreg_q = QuantumRegister(1, 'q')
        creg_c = ClassicalRegister(1, 'c')
        circuit = QuantumCircuit(qreg_q, creg_c)

        circuit.h(qreg_q[0])
        circuit.measure(qreg_q[0], creg_c[0])

        return circuit
    

    def after_circuit_execution(self):
        bitstring = ''.join(self.circuit_result.get_memory())
        result = int(bitstring, base=2)
        self.logger.info(result)
        self.logger.info("Bitstring: %s. Bytes: %b ", bitstring, result)

        self.response.payload = {"bitstring": bitstring, "integer": result}
