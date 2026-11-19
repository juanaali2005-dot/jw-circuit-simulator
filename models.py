"""Six linear RC, RL and RLC state-space circuit models.

Parallel circuits have a voltage source followed by positive series Rs
feeding the parallel branches; this is an explicit modeling assumption.
"""
import numpy as np


def make_model(name, R, L, C, Rs):
    if min(R, L, C, Rs) <= 0:
        raise ValueError('R, L, C and Rs must be positive.')
    def output(coeff, direct=0.0):
        return np.array(coeff, dtype=float), float(direct)
    if name == 'series_rc':
        A, B = [[-1/(R*C)]], [1/(R*C)]
        states = ('capacitor_voltage',)
        outputs = {'capacitor_voltage': output([1]), 'resistor_voltage': output([-1], 1),
                   'circuit_current': output([-1/R], 1/R)}
    elif name == 'series_rl':
        A, B = [[-R/L]], [1/L]
        states = ('inductor_current',)
        outputs = {'inductor_current': output([1]), 'resistor_voltage': output([R]),
                   'inductor_voltage': output([-R], 1)}
    elif name == 'series_rlc':
        A, B = [[-R/L, -1/L], [1/C, 0]], [1/L, 0]
        states = ('inductor_current', 'capacitor_voltage')
        outputs = {'inductor_current': output([1, 0]), 'capacitor_voltage': output([0, 1]),
                   'resistor_voltage': output([R, 0]), 'inductor_voltage': output([-R, -1], 1)}
    elif name == 'parallel_rc':
        A, B = [[-(1/R+1/Rs)/C]], [1/(Rs*C)]
        states = ('node_voltage',)
        outputs = {'node_voltage': output([1]), 'resistor_current': output([1/R]),
                   'capacitor_current': output([-(1/R+1/Rs)], 1/Rs),
                   'source_current': output([-1/Rs], 1/Rs)}
    elif name == 'parallel_rl':
        Rp = R*Rs/(R+Rs)
        A, B = [[-Rp/L]], [Rp/(Rs*L)]
        states = ('inductor_current',)
        outputs = {'inductor_current': output([1]), 'node_voltage': output([-Rp], Rp/Rs),
                   'resistor_current': output([-Rp/R], Rp/(R*Rs)),
                   'source_current': output([Rp/Rs], 1/(R+Rs))}
    elif name == 'parallel_rlc':
        A, B = [[-(1/R+1/Rs)/C, -1/C], [1/L, 0]], [1/(Rs*C), 0]
        states = ('node_voltage', 'inductor_current')
        outputs = {'node_voltage': output([1, 0]), 'inductor_current': output([0, 1]),
                   'resistor_current': output([1/R, 0]),
                   'capacitor_current': output([-(1/R+1/Rs), -1], 1/Rs),
                   'source_current': output([-1/Rs, 0], 1/Rs)}
    else:
        raise ValueError('Unknown circuit: ' + name)
    return np.array(A, dtype=float), np.array(B, dtype=float), states, outputs
