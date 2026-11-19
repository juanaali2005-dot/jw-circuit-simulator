"""Run: py -m unittest -v test_advanced.py"""
import unittest
import numpy as np
from analysis_engine import (CIRCUITS,Excitation,setup,simulate,system_properties,frequency_response,
                             two_parameter_surfaces,time_surface,pole_sweep,quantities,components)

class TestEnhancedCircuitLab(unittest.TestCase):
    p={'R':4.,'L':1.,'C':.1,'Rs':2.}
    def test_all_six_nine_inputs(self):
        for circuit in CIRCUITS:
            _,_,states,outs=setup(circuit,self.p)
            init=[.3]*len(states)
            for kind in ('DC step','Sine AC','DC + sine','Square wave','Triangle wave','Pulse','Ramp','Chirp sweep','Zero input'):
                with self.subTest(circuit=circuit,kind=kind):
                    r=simulate(circuit,self.p,Excitation(kind=kind),init,duration=2.,n=301)
                    self.assertEqual(len(r.t),301)
                    self.assertTrue(np.isfinite(r.states).all())
                    self.assertTrue(all(np.isfinite(v).all() for v in r.outputs.values()))
                    np.testing.assert_allclose(r.states[:,0],init,rtol=0,atol=1e-12)
    def test_one_and_two_order_poles(self):
        for circuit in CIRCUITS:
            A,_,_,_=setup(circuit,self.p)
            props=system_properties(A)
            self.assertEqual(props['order'],1 if 'rlc' not in circuit else 2)
            self.assertTrue(props['stable'])
            if props['order']==1:self.assertGreater(props['tau'],0)
            else:self.assertGreater(props['omega_n'],0)
    def test_all_component_voltages_currents(self):
        for circuit in CIRCUITS:
            _,_,_,outs=setup(circuit,self.p)
            self.assertIn('resistor_voltage',outs)
            self.assertIn('resistor_current',outs)
            self.assertIn('source_current',outs)
            if 'rc' in circuit or 'rlc' in circuit:
                self.assertIn('capacitor_voltage',outs);self.assertIn('capacitor_current',outs)
            if 'rl' in circuit:
                self.assertIn('inductor_current',outs);self.assertIn('inductor_voltage',outs)
            if circuit.startswith('parallel'):
                self.assertIn('source_resistor_voltage',outs)
    def test_dc_steady_states(self):
        for name,target,expect in [('series_rc','capacitor_voltage',10.),('series_rl','inductor_current',2.5),('parallel_rc','node_voltage',20/3),('parallel_rl','node_voltage',0.)]:
            r=simulate(name,self.p,Excitation(),[0.] if 'rlc' not in name else [0,0],12.,n=300)
            self.assertAlmostEqual(r.outputs[target][-1],expect,delta=.005)
    def test_conservation_kvl_kcl(self):
        for circuit in CIRCUITS:
            _,_,states,_=setup(circuit,self.p)
            r=simulate(circuit,self.p,Excitation('DC + sine'),[.2]*len(states),3,300)
            out=r.outputs
            if circuit.startswith('series'):
                parts=out['resistor_voltage']
                if circuit in ('series_rl','series_rlc'):parts=parts+out['inductor_voltage']
                if circuit in ('series_rc','series_rlc'):parts=parts+out['capacitor_voltage']
                np.testing.assert_allclose(parts,r.source,rtol=0,atol=1e-9)
            else:
                currents=out['resistor_current']
                if circuit in ('parallel_rc','parallel_rlc'):currents=currents+out['capacitor_current']
                if circuit in ('parallel_rl','parallel_rlc'):currents=currents+out['inductor_current']
                np.testing.assert_allclose(currents,out['source_current'],atol=1e-9)
                np.testing.assert_allclose(out['source_resistor_voltage']+out['node_voltage'],r.source,atol=1e-9)
    def test_frequency_dc_matches_steady(self):
        for circuit in CIRCUITS:
            A,B,states,outs=setup(circuit,self.p)
            for name,(c,d) in outs.items():
                H=frequency_response(circuit,self.p,name,[0])[0]
                target=(c@np.linalg.solve(-A,B)+d)
                np.testing.assert_allclose(H,target,atol=1e-10)
    def test_two_variable_3d_all_outputs(self):
        A,B,states,outs=setup('series_rlc',self.p)
        xx=np.array([2.,4.,6.]);yy=np.array([.5,1.])
        gr=two_parameter_surfaces('series_rlc',self.p,Excitation(),(0.,0.),'R',xx,'L',yy,
                                list(outs),'Value at selected time',.8,duration=1.2,samples=90)
        self.assertEqual(len(gr),len(outs))
        for v in gr.values():self.assertEqual(v.shape,(2,3));self.assertTrue(np.isfinite(v).all())
        self.assertFalse(np.allclose(gr['capacitor_voltage'][:,0],gr['capacitor_voltage'][:,-1]))
    def test_time_surface_and_pole_sweep(self):
        t,y,z=time_surface('parallel_rc',self.p,Excitation(),[0.], 'C',.04,.12,
                            'capacitor_voltage',2.,100,6)
        self.assertEqual(z.shape,(6,100))
        rows=pole_sweep('series_rlc',self.p,'R',[1,2,3])
        self.assertEqual(len(rows),6)
        self.assertTrue(all(row['real']<0 for row in rows))
    def test_reject_invalid_samples(self):
        with self.assertRaisesRegex(ValueError,'Increase samples'):
            simulate('series_rc',self.p,Excitation('Chirp sweep',chirp_end_hz=8.),[0],20,100)
    def test_first_order_tau_theoretical(self):
        A,_,_,_=setup('series_rc',self.p)
        self.assertAlmostEqual(system_properties(A)['tau'],self.p['R']*self.p['C'])
        A,_,_,_=setup('series_rl',self.p)
        self.assertAlmostEqual(system_properties(A)['tau'],self.p['L']/self.p['R'])
    def test_r_l_c_parameter_effect_on_damping(self):
        z=[]
        for r in [1,2,4,8]:
            A,_,_,_=setup('series_rlc',{**self.p,'R':r})
            z.append(system_properties(A)['zeta'])
        self.assertTrue(all(a<b for a,b in zip(z,z[1:])))

if __name__=='__main__':unittest.main()
