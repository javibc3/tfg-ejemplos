# -*- coding: utf-8 -*-
# zato: ide-deploy=True
import math
import json
from collections import Counter
from fractions import Fraction
from typing import Any, Dict, List

from zato.server.service import Service


class ShorPostProcesing(Service):

    name = 'shor.shor-post-procesing'

    def handle(self) -> None:
        input = json.loads(self.request.payload)
        results = {
            "measurement_counts": input.get('measurement_counts'),
        }
        factors = self.get_factors_from_results(results, int(input.get('N')), int(input.get('a')), True)
        self.logger.info(str(factors))
        self.response.payload = str(factors)

    def get_factors_from_results(
        self,
        results: Dict[str, Any],
        integer_N: int,
        integer_a: int,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Function to postprocess dictionary returned by run_shors_algorithm
            and pretty print results

        Args:
            results (Dict[str, Any]): Results associated with quantum phase estimation run as produced
                by run_shors_algorithm
            integer_N (int) : The integer to be factored
            integer_a (int) : Any integer that satisfies 1 < a < N and gcd(a, N) = 1.
            verbose (bool) : If True, prints aggregate results (default is False)
        Returns:
            Dict[str, Any]: Factors of the integer N
        """

        # unpack results
        measurement_counts = Counter(results["measurement_counts"])

        # get phases
        phases_decimal = self._get_phases(measurement_counts)

        r_guesses = []
        factors = []
        if verbose:
            print(f"Number of Measured phases (s/r) : {len(phases_decimal)}")
        for phase in phases_decimal:
            if verbose:
                print(f"\nFor phase {phase} :")
            r = (Fraction(phase).limit_denominator(integer_N)).denominator
            r_guesses.append(r)
            if verbose:
                print(f"Estimate for r is : {r}")
            factor = [
                math.gcd(integer_a ** (r // 2) - 1, integer_N),
                math.gcd(integer_a ** (r // 2) + 1, integer_N),
            ]
            factors.append(factor[0])
            factors.append(factor[1])
            if verbose:
                print(f"Factors are : {factor[0]} and {factor[1]}")
        factors_set = set(factors)
        factors_set.discard(1)
        factors_set.discard(integer_N)
        if verbose:
            print(f"\n\nNon-trivial factors found are : {factors_set}")

        aggregate_results = {"guessed_factors": factors_set}

        return aggregate_results


    def _get_phases(self, measurement_counts: Counter) -> List[float]:
        """
        Get phase estimate from measurement_counts using top half qubits

        Args:
            measurement_counts (Counter) : measurement results from a device run
        Returns:
            List[float] : decimal phase estimates
        """

        # Aggregate the results (i.e., ignore/trace out the query register qubits):
        if not measurement_counts:
            return None

        # First get bitstrings with corresponding counts for counting qubits only (top half)
        num_counting_qubits = int(len(list(measurement_counts.keys())[0]) / 2)

        bitstrings_precision_register = [key[:num_counting_qubits] for key in measurement_counts.keys()]

        # Then keep only the unique strings
        bitstrings_precision_register_set = set(bitstrings_precision_register)
        # Cast as a list for later use
        bitstrings_precision_register_list = list(bitstrings_precision_register_set)

        # Now create a new dict to collect measurement results on the precision_qubits. Keys are given
        # by the measurement count substrings on the register qubits. Initialize the counts to zero.
        precision_results_dict = {key: 0 for key in bitstrings_precision_register_list}

        # Loop over all measurement outcomes
        for key in measurement_counts.keys():
            # Save the measurement count for this outcome
            counts = measurement_counts[key]
            # Generate the corresponding shortened key (supported only on the precision_qubits register)
            count_key = key[:num_counting_qubits]
            # Add these measurement counts to the corresponding key in our new dict
            precision_results_dict[count_key] += counts

        phases_decimal = [self._binary_to_decimal(item) for item in precision_results_dict.keys()]

        return phases_decimal


    def _binary_to_decimal(self, binary: str) -> float:
        """
        Helper function to convert binary string (example: '01001') to decimal

        Args:
            binary (str): value to convert to decimal fraction

        Returns:
            float: decimal value
        """

        fracDecimal = 0

        # Convert fractional part of binary to decimal equivalent
        twos = 2

        for ii in range(len(binary)):
            fracDecimal += (ord(binary[ii]) - ord("0")) / twos
            twos *= 2.0

        # return fractional part
        return fracDecimal