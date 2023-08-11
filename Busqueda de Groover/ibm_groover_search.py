# -*- coding: utf-8 -*-
# zato: ide-deploy=True
import json
from typing import Tuple

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


# Zato
from zato.server.service import IBMQuantumService

# ##############################################################################

class GrooverSearch(IBMQuantumService):
    """ Returns details of a user by the person's ID.
    """
    name = 'ibm_quantum.groover-search'
    runs = 100
    quantum_computer = 'ibmq_qasm_simulator'
    key_name = 'ibm_quantum'
    threshold = 0.8

    def circuit(self):

        qreg_q = QuantumRegister(2, 'q')
        creg_c = ClassicalRegister(2, 'c')
        circuit = QuantumCircuit(qreg_q, creg_c)

        circuit.h(qreg_q[1])
        circuit.h(qreg_q[0])
        circuit.x(qreg_q[1])
        circuit.x(qreg_q[0])
        circuit.cz(qreg_q[0], qreg_q[1])
        circuit.x(qreg_q[0])
        circuit.x(qreg_q[1])
        circuit.h(qreg_q[0])
        circuit.h(qreg_q[1])
        circuit.z(qreg_q[0])
        circuit.z(qreg_q[1])
        circuit.cz(qreg_q[0], qreg_q[1])
        circuit.h(qreg_q[0])
        circuit.h(qreg_q[1])
        circuit.measure(qreg_q[0], creg_c[0])
        circuit.measure(qreg_q[1], creg_c[1])

        return circuit
    

    def after_circuit_execution(self):
        self.logger.info(str(self.circuit_result.get_counts()))
        self.response.payload = str(self.circuit_result.get_counts())
