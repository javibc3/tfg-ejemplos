# -*- coding: utf-8 -*-
# zato: ide-deploy=True
import json
import numpy as np
from typing import List

from scipy.optimize import minimize
from qaoaQrngInput import Output
from qaoa import Input

from zato.server.service import Service


class QaoaCostFunction(Service):

    name = 'qaoa.qaoa-cost-function'

    input = Output

    def handle(self):

        input = self.request.input
        self.coupling_matrix = input.matrix
        self.n_qubits = input.n_qubits
        self.n_layers = input.n_layers

        self.coupling_matrix = np.array(self.coupling_matrix, dtype=float)

        np.fill_diagonal(self.coupling_matrix, 0)

        idx = self.coupling_matrix.nonzero()
        coeffs = [self.coupling_matrix[qubit_pair] for qubit_pair in zip(idx[0], idx[1])]

        init_values = np.random.rand(2 * self.n_layers)

        losses = []
        result = minimize(
                self.cost_function,
                init_values,
                args=(coeffs, losses, 0),  # shots=0
                options={"disp": True, "maxfev": 150},
                method="Nelder-Mead",
        # bounds=bounds, # optional, some optimizers can use bounds
        )
        self.logger.info(str(losses))
        self.invoke_async('qaoa.qaoa-create-image', json.dumps(losses))
        
    def cost_function(
        self,
        values: np.ndarray,
        coeffs: np.ndarray,
        cost_history: List[float],
        shots: int = 0
    ) -> float:
        """Cost function and append to loss history list.

        Args:
            values (ndarray): Values for the parameters.
            device (Device): Braket device to run on.
            circ (Circuit): QAOA circuit to run.
            coeffs (ndarray): The coefficients of the cost Hamiltonian.
            cost_history (List[float]): History of cost evaluations.
            shots (int): Number of shots. Defaults to 0.

        Returns:
            float: The cost function value
        """
        request = Input()
        request.n_qubits = self.n_qubits
        request.n_layers = self.n_layers
        request.matrix = self.coupling_matrix
        request.values = values
        response = self.invoke('qaoa.qaoa', request)
        exp_vals = response.result.result_types
        cost = sum(c * s.value for c, s in zip(coeffs, exp_vals))
        cost_history.append(cost)
        return cost