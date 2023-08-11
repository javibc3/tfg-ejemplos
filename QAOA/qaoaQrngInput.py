# -*- coding: utf-8 -*-
# zato: ide-deploy=True
from dataclasses import dataclass
import struct

import numpy as np

from zato.server.service import Service, Model

@dataclass(init=False)
class Output(Model):
    n_qubits: int
    n_layers: int
    matrix: list

class QaoaQrngInput(Service):

    name = 'qaoa.qaoa-qrng-input'
    output = Output

    def handle(self):

        n_qubits = self.request.payload['n_qubits']
        n_layers = self.request.payload['n_layers']

        ising_matrix = np.zeros((n_qubits, n_qubits))

        for i in range(n_qubits):
            for j in range(n_qubits):
                result = self.invoke('quantum.qrng', runs=10)
                ising_matrix[i, j] = result["integer"]
        
        normalized_matrix = (ising_matrix-(np.min(ising_matrix)))/(np.max(ising_matrix)-np.min(ising_matrix))

        output = Output()
        output.matrix = normalized_matrix.tolist()
        output.n_layers = n_layers
        output.n_qubits = n_qubits

        self.invoke('qaoa.qaoa-cost-function', output)
