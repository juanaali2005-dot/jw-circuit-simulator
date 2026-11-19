"""Advanced electric-circuit analysis for the Jwana Streamlit teaching project.

Six physically defined state-space models are imported from models.py.
All R/L/C elements are ideal and linear. The parallel source goes through Rs.
The AC frequency input is in Hz and converted to angular frequency internally.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from scipy.signal import sawtooth, square
from scipy.signal import ss2tf
from models import make_model

CIRCUITS = ('series_rc', 'series_rl', 'series_rlc', 'parallel_rc', 'parallel_rl', 'parallel_rlc')
INPUTS = ('DC step', 'Sine AC', 'DC + sine', 'Square wave', 'Triangle wave', 'Pulse', 'Ramp', 'Chirp sweep', 'Zero input')
PARAMS = ('R', 'L', 'C', 'Rs')


def quantities(circuit: str, outputs):
    """Supply all element voltages, element currents and source-resistor quantities.

    Each output is a (C row, D scalar) for y = C*x + D*u.
    The base model already defines the state-space matrices, and these additions
    are derived from KCL/KVL rather than introducing alternative physics.
    """
    result = {k: (np.asarray(c, dtype=float), float(d)) for k,(c,d) in outputs.items()}
    def alias(name, other): result[name] = result[other]
    if circuit == 'series_rc':
        alias('resistor_current','circuit_current')
        alias('capacitor_current','circuit_current')
        alias('source_current','circuit_current')
    elif circuit == 'series_rl':
        alias('resistor_current','inductor_current')
        alias('source_current','inductor_current')
    elif circuit == 'series_rlc':
        alias('resistor_current','inductor_current')
        alias('capacitor_current','inductor_current')
        alias('source_current','inductor_current')
    elif circuit == 'parallel_rc':
        alias('resistor_voltage','node_voltage')
        alias('capacitor_voltage','node_voltage')
        c,d=result['node_voltage']
        result['source_resistor_voltage']=(-c,1.0-d)
    elif circuit == 'parallel_rl':
        alias('resistor_voltage','node_voltage')
        alias('inductor_voltage','node_voltage')
        c,d=result['node_voltage']
        result['source_resistor_voltage']=(-c,1.0-d)
    else:
        alias('resistor_voltage','node_voltage')
        alias('capacitor_voltage','node_voltage')
        alias('inductor_voltage','node_voltage')
        c,d=result['node_voltage']
        result['source_resistor_voltage']=(-c,1.0-d)
    return result


def setup(circuit: str, p: dict):
    A,B,states,outputs=make_model(circuit,p['R'],p['L'],p['C'],p['Rs'])
    return A,B,states,quantities(circuit,outputs)


def output_units(name):
    return 'A' if name.endswith('_current') else 'V'


def pretty(name):
    return f"{name.replace('_',' ').title()} ({output_units(name)})"


def components(circuit):
    return [x for x in ('R', 'L', 'C') if x.lower() in circuit.split('_')[1]] + (['Rs'] if circuit.startswith('parallel') else [])


@dataclass(frozen=True)
class Excitation:
    kind: str = 'DC step'
    dc: float = 10.0
    amplitude: float = 8.0
    f_hz: float = 0.5
    phase_deg: float = 0.0
    duty: float = 0.35
    pulse_start: float = 0.5
    pulse_width: float = 1.0
    ramp_slope: float = 3.0
    chirp_end_hz: float = 5.0
    chirp_duration: float = 8.0

    def value(self, t):
        a=np.asarray(t,dtype=float)
        omega=2*np.pi*self.f_hz
        phase=np.deg2rad(self.phase_deg)
        if self.kind == 'DC step': u=np.full_like(a,self.dc)
        elif self.kind == 'Sine AC': u=self.amplitude*np.sin(omega*a+phase)
        elif self.kind == 'DC + sine': u=self.dc+self.amplitude*np.sin(omega*a+phase)
        elif self.kind == 'Square wave': u=self.amplitude*square(omega*a+phase,duty=self.duty)
        elif self.kind == 'Triangle wave': u=self.amplitude*sawtooth(omega*a+phase,width=0.5)
        elif self.kind == 'Pulse': u=self.amplitude*((a>=self.pulse_start)&(a<self.pulse_start+self.pulse_width))
        elif self.kind == 'Ramp': u=self.ramp_slope*a
        elif self.kind == 'Chirp sweep':
            # Linear sweep instantaneous frequency f(t) = f0 + (f1-f0)*t/T.
            rate=(self.chirp_end_hz-self.f_hz)/self.chirp_duration
            u=self.amplitude*np.sin(2*np.pi*(self.f_hz*a+0.5*rate*a*a)+phase)
        elif self.kind == 'Zero input': u=np.zeros_like(a)
        else: raise ValueError('Unknown input '+str(self.kind))
        return float(u) if u.ndim==0 else u


@dataclass
class Response:
    t: np.ndarray
    source: np.ndarray
    state_names: tuple
    states: np.ndarray
    outputs: dict
    A: np.ndarray
    B: np.ndarray


def simulate(circuit: str, p: dict, exc: Excitation, x0, duration=8., n=601):
    """Numerical response for any of nine source waveforms, with nonzero states."""
    if duration<=0 or n<3 or n>10001: raise ValueError('Invalid simulation time/sample count')
    A,B,states,outs=setup(circuit,p)
    x0=np.asarray(x0,dtype=float)
    if x0.shape!=(len(states),): raise ValueError('Initial-condition vector has wrong size')
    if not np.isfinite(x0).all(): raise ValueError('Initial conditions must be finite')
    t=np.linspace(0,float(duration),int(n))
    maxf=exc.f_hz
    if exc.kind=='Chirp sweep': maxf=max(exc.f_hz,exc.chirp_end_hz)
    if exc.kind in ('Sine AC','DC + sine','Square wave','Triangle wave','Chirp sweep') and maxf>0:
        if n/max(duration*maxf,1e-9)<22: raise ValueError('Increase samples to at least 22 per input cycle')
    step=duration/260
    if exc.kind in ('Sine AC','DC + sine','Square wave','Triangle wave','Chirp sweep') and maxf>0:
        step=min(step,1/(35*maxf))
    sol=solve_ivp(lambda z,x: A@x+B*exc.value(z),[0,duration],x0,t_eval=t,
                  method='LSODA',rtol=1e-7,atol=1e-9,max_step=step)
    if not sol.success: raise ValueError('Solver failed: '+sol.message)
    u=np.asarray(exc.value(t))
    values={name:co@sol.y+d*u for name,(co,d) in outs.items()}
    return Response(t,u,states,sol.y,values,A,B)


def system_properties(A):
    """Return system order, eigenvalue poles and dynamical interpretation."""
    eig=np.linalg.eigvals(A)
    if A.shape[0]==1:
        r=float(np.real(eig[0]));return {'order':1,'poles':eig,'tau':-1/r if r<0 else float('inf'),
            'stable':bool(np.all(np.real(eig)<0))}
    poly=np.poly(A)
    wn=np.sqrt(float(poly[-1])) if poly[-1]>0 else float('nan')
    zeta=float(poly[1]/(2*wn)) if wn>0 else float('nan')
    if zeta<1-1e-6: status='Underdamped'
    elif zeta>1+1e-6:status='Overdamped'
    else:status='Critically damped'
    return {'order':2,'poles':eig,'omega_n':wn,'freq_n_hz':wn/(2*np.pi),'zeta':zeta,
            'damping':status,'settling_est':4/(zeta*wn) if zeta>0 else float('inf'),
            'stable':bool(np.all(np.real(eig)<0))}


def frequency_response(circuit,p,output,freq):
    """Complex zero-state transfer function H(j2πf) for a selected output."""
    A,B,states,outs=setup(circuit,p)
    c,d=outs[output]
    eye=np.eye(A.shape[0])
    result=np.array([c @ np.linalg.solve(1j*2*np.pi*float(f)*eye-A,B)+d for f in np.asarray(freq)],dtype=complex)
    return result


def transfer_function(circuit,p,output):
    A,B,states,outs=setup(circuit,p);c,d=outs[output]
    num,den=ss2tf(A,B[:,None],c[None,:],np.array([[d]]))
    return num[0],den


def metric(values,t,metric_type,observe_t):
    if metric_type=='Value at selected time': return float(np.interp(observe_t,t,values))
    if metric_type=='Peak absolute value': return float(np.max(np.abs(values)))
    if metric_type=='RMS over window': return float(np.sqrt(np.mean(np.asarray(values)**2)))
    if metric_type=='Peak-to-peak':return float(np.ptp(values))
    raise ValueError(metric_type)


def time_surface(circuit,p,exc,x0,param,lo,hi,output,duration=6.,points=220,steps=17):
    """Return 3D surface z=measured output, x=time, y=selected parameter."""
    axis=np.linspace(lo,hi,steps)
    surface=[]
    t=None
    for val in axis:
        q=p.copy();q[param]=float(val)
        r=simulate(circuit,q,exc,x0,duration,points)
        t=r.t
        surface.append(r.outputs[output])
    return t,axis,np.asarray(surface)


def two_parameter_surface(circuit,p,exc,x0,px,xs,py,ys,output,metric_type,observe_t,duration=6.,samples=220):
    """Return z=output metric for any two component values, not a screenshot."""
    z=np.zeros((len(ys),len(xs)))
    for i,y in enumerate(ys):
        for j,x in enumerate(xs):
            q=p.copy();q[px]=float(x);q[py]=float(y)
            res=simulate(circuit,q,exc,x0,duration,samples)
            z[i,j]=metric(res.outputs[output],res.t,metric_type,observe_t)
    return z


def pole_sweep(circuit,p,parameter,values):
    pole_rows=[]
    for v in values:
        q=p.copy();q[parameter]=float(v)
        A,_,_,_=setup(circuit,q)
        lam=np.linalg.eigvals(A)
        for i,l in enumerate(sorted(lam,key=lambda z:z.imag)):
            pole_rows.append({'parameter_value':float(v),'pole_number':i+1,'real':float(l.real),'imag':float(l.imag)})
    return pole_rows


def two_parameter_surfaces(circuit,p,exc,x0,px,xs,py,ys,output_names,metric_type,observe_t,duration=6.,samples=180):
    """Calculate multiple output surfaces using one ODE solve per grid point."""
    grids={name:np.zeros((len(ys),len(xs))) for name in output_names}
    for i,y in enumerate(ys):
        for j,x in enumerate(xs):
            q=p.copy();q[px]=float(x);q[py]=float(y)
            res=simulate(circuit,q,exc,x0,duration,samples)
            for name in output_names:
                grids[name][i,j]=metric(res.outputs[name],res.t,metric_type,observe_t)
    return grids
