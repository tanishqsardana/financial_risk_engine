# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""
Cython inner loop for Monte Carlo portfolio simulation.
Caller is responsible for generating standard-normal samples (z) via numpy.
This module handles simulated portofio risk + return loop
without any Python overhead or intermediate array allocation.
"""
import numpy as np
cimport numpy as np

np.import_array()


def simulate_returns_cython(
    double[:] mu,
    double[:, :] L,
    double[:] weights,
    double[:, :] z,
) -> np.ndarray:
    cdef int n_sims = z.shape[0]
    cdef int n = z.shape[1]
    cdef int sim, i, j
    cdef double port_ret, asset_ret
    cdef double[:] port_returns = np.empty(n_sims, dtype=np.float64)

    for sim in range(n_sims):
        port_ret = 0.0
        for i in range(n):
            asset_ret = mu[i]
            for j in range(n):
                asset_ret = asset_ret + L[i, j] * z[sim, j]
            port_ret = port_ret + weights[i] * asset_ret
        port_returns[sim] = port_ret

    return np.asarray(port_returns)
