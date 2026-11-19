"""Optional: generate example 3D figures (not needed for Streamlit)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from analysis_engine import Excitation,setup,system_properties,pole_sweep,two_parameter_surfaces,frequency_response

root=Path(__file__).parent/'examples'
p={'R':4.,'L':1.,'C':.1,'Rs':2.}
xx=np.linspace(1,12,15);yy=np.linspace(.03,.2,15)
res=two_parameter_surfaces('series_rc',p,Excitation(),(1.2,),'R',xx,'C',yy,['capacitor_voltage','resistor_current'],'Value at selected time',1,2,150)
fig=plt.figure(figsize=(9,6),dpi=130);ax=fig.add_subplot(projection='3d')
X,Y=np.meshgrid(xx,yy*1000)
sf=ax.plot_surface(X,Y,res['capacitor_voltage'],cmap='viridis',linewidth=0,antialiased=True)
fig.colorbar(sf,shrink=.7,pad=.14,label='Capacitor voltage (V)')
ax.set(xlabel='Resistance (Ω)',ylabel='Capacitance (mF)',zlabel='Capacitor voltage (V)',title='Series RC — Two-variable sweep at t=1 s (DC 10 V)')
fig.tight_layout();fig.savefig(root/'example_RC_two_variable_surface.png',bbox_inches='tight');plt.close(fig)

fig=plt.figure(figsize=(9,6),dpi=130);ax=fig.add_subplot(projection='3d')
sf=ax.plot_surface(X,Y,res['resistor_current'],cmap='plasma',linewidth=0,antialiased=True)
fig.colorbar(sf,shrink=.7,pad=.14,label='Resistor current (A)')
ax.set(xlabel='Resistance (Ω)',ylabel='Capacitance (mF)',zlabel='Resistor current (A)',title='Series RC — Current response vs R and C, t=1 s')
fig.tight_layout();fig.savefig(root/'example_RC_current_surface.png',bbox_inches='tight');plt.close(fig)

pr=pole_sweep('series_rlc',p,'R',np.linspace(1,15,65))
fig,ax=plt.subplots(figsize=(8,5),dpi=120)
ax.scatter([k['real'] for k in pr],[k['imag'] for k in pr],c=[k['parameter_value'] for k in pr],cmap='viridis',s=20)
ax.axvline(0,color='red',lw=1,ls='--');ax.grid(alpha=.25)
ax.set(xlabel='Real pole (s⁻¹)',ylabel='Imag pole (rad/s)',title='Second-order RLC poles as R changes')
fig.tight_layout();fig.savefig(root/'example_RLC_pole_movement.png');plt.close(fig)
print('Preview figures written:',len(list(root.glob('*.png'))))
