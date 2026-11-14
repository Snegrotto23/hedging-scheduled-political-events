"""
Quitar el margen (overround) de cuotas o precios.

Entrada: lista de "probabilidades brutas" pi_i = 1/cuota_decimal (o precio del contrato en un exchange).
- proporcional: p_i = pi_i / sum(pi)
- Shin (1992, 1993): p_i(z) = [sqrt(z^2 + 4(1-z) pi_i^2 / Pi) - z] / [2(1-z)], Pi = sum(pi);
  z (proporción de insiders) se resuelve para que sum p_i(z) = 1.
  Con dos resultados, Shin corre la probabilidad hacia el favorito (corrige el sesgo favorito-longshot).
Si sum(pi) <= 1 (sin margen o precios por debajo de 1), Shin no aplica y se devuelve el proporcional.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq


def proportional(pi):
    pi = np.asarray(pi, float)
    return pi / pi.sum()


def shin(pi):
    pi = np.asarray(pi, float)
    Pi = pi.sum()
    if Pi <= 1 + 1e-12:
        return pi / Pi, 0.0

    def probs(z):
        return (np.sqrt(z * z + 4 * (1 - z) * pi * pi / Pi) - z) / (2 * (1 - z))

    z = brentq(lambda z: probs(z).sum() - 1, 0.0, 0.999)
    p = probs(z)
    return p / p.sum(), float(z)


def from_odds(odds):
    return [1.0 / o for o in odds]


if __name__ == "__main__":
    # chequeo con cuotas de Brasil 2022 (bet365 28/10: Lula 1,44, Bolsonaro 2,62)
    pi = from_odds([1.44, 2.62])
    print("overround", sum(pi) - 1, "prop", proportional(pi), "shin", shin(pi))
