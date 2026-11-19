"""Jwana CircuitLab Pro: first/second order + 3D + poles + sweeping.

To start: py -m streamlit run app.py
"""
from __future__ import annotations

from io import BytesIO
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from diagram import circuit_diagram
from analysis_engine import (
    CIRCUITS, PARAMS, Excitation, setup, simulate, pretty, output_units,
    system_properties, frequency_response, transfer_function, components,
    two_parameter_surfaces, time_surface, pole_sweep,
)

st.set_page_config(page_title='Jwana CircuitLab Pro', page_icon='⚡', layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.45rem;max-width:1450px;}
div[data-testid="stMetric"]{border:1px solid #c5d8dc;border-radius:12px;padding:14px;}
.smallnote{color:#657888;font-size:.9rem;}
</style>''',unsafe_allow_html=True)
st.title('⚡ Jwana CircuitLab Pro — Dynamic Control Systems Simulator')
st.caption('Six RC/RL/RLC models · All element voltages and currents · First/second order · 3D sweeps · Poles · Frequency analysis')

with st.sidebar:
    st.header('1 · Choose circuit')
    family=st.selectbox('Circuit type',['RC','RL','RLC'],index=2)
    connection=st.radio('Connection',['Series','Parallel'],horizontal=True)
    circuit=f'{connection.lower()}_{family.lower()}'
    st.header('2 · Adjust R, L, C')
    R=st.slider('Resistance R (Ω)',1.0,100.0,4.0,1.0)
    L=st.slider('Inductance L (H)',.1,10.0,1.0,.1,disabled='L' not in family)
    C_mF=st.slider('Capacitance C (mF)',1,200,100,1,disabled='C' not in family)
    Rs=st.slider('Source resistance Rs (Ω)',.5,50.0,2.0,.5,disabled=connection=='Series')
    p={'R':R,'L':L,'C':C_mF/1000.0,'Rs':Rs}
    st.header('3 · Input waveform')
    wave=st.selectbox('Applied voltage',['DC step','Sine AC','DC + sine','Square wave','Triangle wave','Pulse','Ramp','Chirp sweep','Zero input'])
    dc=st.slider('DC voltage (V)',-30.,30.,10.,.5,disabled=wave not in ('DC step','DC + sine'))
    amp=st.slider('AC / pulse amplitude (V peak)',0.,30.,8.,.5,disabled=wave in ('DC step','Ramp','Zero input'))
    freq=st.slider('Start / fixed frequency (Hz)',.1,8.,.5,.1,disabled=wave not in ('Sine AC','DC + sine','Square wave','Triangle wave','Chirp sweep'))
    phase=st.slider('AC phase (degrees)',-180,180,0,15,disabled=wave not in ('Sine AC','DC + sine','Square wave','Triangle wave','Chirp sweep'))
    duty=st.slider('Square-wave duty cycle',.1,.9,.35,.05) if wave=='Square wave' else .35
    pulse_start=st.slider('Pulse start (seconds)',0.,10.,.5,.1) if wave=='Pulse' else .5
    pulse_width=st.slider('Pulse width (seconds)',.1,10.,1.,.1) if wave=='Pulse' else 1.
    slope=st.slider('Ramp slope (V/s)',-10.,10.,3.,.5) if wave=='Ramp' else 3.
    f_end=st.slider('Chirp end frequency (Hz)',.1,8.,5.,.1) if wave=='Chirp sweep' else 5.
    st.header('4 · Initial conditions')
    A,B,states,output_defs=setup(circuit,p)
    x0=[]
    for state in states:
        if state.endswith('current'):
            x0.append(st.slider(f'Initial {state.replace("_"," ")} (A)',-5.,5.,.25,.05,key='ic_'+circuit+'_'+state))
        else:
            x0.append(st.slider(f'Initial {state.replace("_"," ")} (V)',-30.,30.,1.2,.2,key='ic_'+circuit+'_'+state))
    st.header('5 · Time settings')
    duration=st.slider('Duration (s)',.5,20.,6.,.5)
    points=st.slider('Graph samples',301,4001,1201,100)

exc=Excitation(wave,dc,amp,freq,phase,duty,pulse_start,pulse_width,slope,f_end,duration)
try:
    with st.spinner('Calculating circuit response...'):
        res=simulate(circuit,p,exc,x0,duration,points)
except (ValueError,RuntimeError) as e:
    st.error(f'The current settings cannot be simulated: {e}')
    st.info('Try increasing Graph samples or reducing frequency/duration.')
    st.stop()
props=system_properties(A)

c1,c2,c3,c4=st.columns(4)
c1.metric('Circuit',f'{connection} {family}')
c2.metric('System order',f'{props["order"]} — {"first" if props["order"]==1 else "second"} order')
if props['order']==1:
    c3.metric('Time constant τ',f'{props["tau"]:.4g} s')
    c4.metric('Pole',f'{np.real(props["poles"][0]):.4g} s⁻¹')
else:
    c3.metric('Natural frequency ωₙ',f'{props["omega_n"]:.4g} rad/s')
    c4.metric('Damping ratio ζ',f'{props["zeta"]:.3f}')

show_diagram,system_tab,surf_time_tab,surf_two_tab,freq_tab,export_tab=st.tabs([
    '🔌 Circuit & response','📍 System order & poles','🌀 3D time surface',
    '🗺️ 3D two-variable sweep','〰️ Frequency & sweeping','📥 All data & export'])

with show_diagram:
    st.subheader(f'{connection} {family}: electrical schematic')
    fig=circuit_diagram(family,connection)
    st.pyplot(fig,clear_figure=False)
    plt.close(fig)
    if connection=='Parallel':
        st.info('Physics assumption: the ideal voltage source drives the parallel branches through a positive series resistor Rs. This permits meaningful parallel-node dynamics.')
    st.subheader('Plot any element voltage or current')
    all_names=list(res.outputs)
    default=[n for n in ('capacitor_voltage','node_voltage','inductor_current','resistor_voltage') if n in res.outputs]
    chosen=st.multiselect('Select one, multiple or all outputs',all_names,default=default[:3] or all_names[:2],format_func=pretty,key='timeselect')
    if st.checkbox('All output traces',False,key='alltime'):chosen=all_names
    for unit in ('V','A'):
        names=[n for n in chosen if output_units(n)==unit]
        if not names:continue
        fig2=go.Figure()
        if unit=='V':fig2.add_scatter(x=res.t,y=res.source,mode='lines',name='Source voltage',line=dict(color='gray',dash='dash'))
        for name in names: fig2.add_scatter(x=res.t,y=res.outputs[name],mode='lines',name=pretty(name))
        fig2.update_layout(title=f'{unit} outputs over time',xaxis_title='Time (s)',yaxis_title=f'{"Voltage" if unit=="V" else "Current"} ({unit})',height=400,legend=dict(orientation='h',y=-.3))
        st.plotly_chart(fig2,use_container_width=True)
        st.download_button(f'Download {unit} graph (interactive HTML)',fig2.to_html(include_plotlyjs=True).encode('utf-8'),file_name=f'{circuit}_{unit}_time.html',mime='text/html',key='download_time_'+unit)
    st.subheader('Input waveform and internal state variables')
    wave_fig=go.Figure()
    wave_fig.add_scatter(x=res.t,y=res.source,name='u(t)',line_color='gray')
    wave_fig.update_layout(height=250,xaxis_title='Time (s)',yaxis_title='Input (V)')
    st.plotly_chart(wave_fig,use_container_width=True)
    for i,n in enumerate(states):
        states_fig=go.Figure()
        states_fig.add_scatter(x=res.t,y=res.states[i],name=pretty(n))
        states_fig.update_layout(title=f'State trajectory: {pretty(n)}',height=240,xaxis_title='Time (s)',yaxis_title=pretty(n))
        st.plotly_chart(states_fig,use_container_width=True,key=f'state_plot_{i}')
    if len(states)==2:
        phase_fig=go.Figure(go.Scatter(x=res.states[0],y=res.states[1],mode='lines+markers',marker=dict(size=3,color=res.t,colorscale='Viridis',showscale=True,colorbar=dict(title='t (s)')),name='Trajectory'))
        phase_fig.update_layout(title='2D state-space phase trajectory',xaxis_title=pretty(states[0]),yaxis_title=pretty(states[1]),height=340)
        st.plotly_chart(phase_fig,use_container_width=True)

with system_tab:
    st.subheader('First-order versus second-order system characteristics')
    st.write(f'**State vector:** {", ".join(states)}')
    st.latex(r'\dot{x}=Ax+Bu,\quad y=C_ox+Du')
    colA,colB=st.columns(2)
    colA.write('**State dynamics matrix A**');colA.dataframe(pd.DataFrame(A),hide_index=True)
    colB.write('**Input matrix B**');colB.dataframe(pd.DataFrame(B[:,None]),hide_index=True)
    pole_df=pd.DataFrame({'Real part (1/s)':np.real(props['poles']),'Imaginary part (rad/s)':np.imag(props['poles'])})
    st.write('**Eigenvalues / system poles:**');st.dataframe(pole_df,hide_index=True)
    st.write('**Stable?**','Yes: all poles have negative real parts' if props['stable'] else 'Not asymptotically stable')
    if props['order']==1:
        st.latex(r'x(t)=x_{ss}+[x(0)-x_{ss}]e^{-t/\tau},\qquad \tau=-1/\lambda')
        st.write(f'First order: one energy-storage state, pole λ={np.real(props["poles"][0]):.4g}, time constant τ={props["tau"]:.4g} s.')
    else:
        st.latex(r's^2+2\zeta\omega_n s+\omega_n^2=0')
        st.write(f'**Damping classification:** {props["damping"]}. Natural frequency {props["omega_n"]:.4g} rad/s ({props["freq_n_hz"]:.4g} Hz); damping ζ={props["zeta"]:.4g}; approximate 2% settling time 4/(ζωₙ)={props["settling_est"]:.4g} s (dominant-second-order estimate, not an exact measured value).')
    figp=go.Figure()
    figp.add_vline(x=0,line_dash='dash',line_color='red')
    figp.add_scatter(x=np.real(props['poles']),y=np.imag(props['poles']),mode='markers',marker=dict(size=16,symbol='x',color='#dc2626',line=dict(width=2)),name='Poles')
    figp.update_layout(title='Complex s-plane pole locations',xaxis_title='Real(s) (1/s)',yaxis_title='Imag(s) (rad/s)',height=365)
    st.plotly_chart(figp,use_container_width=True)
    st.subheader('Output transfer function, selected output')
    transfer_output=st.selectbox('Output to inspect',list(output_defs),format_func=pretty,key='tfout')
    num,den=transfer_function(circuit,p,transfer_output)
    co,do=output_defs[transfer_output]
    st.write('Cₒ =',co[None,:],'D =',do)
    st.code(f'Numerator coefficients: {np.array2string(num,precision=5)}\nDenominator coefficients: {np.array2string(den,precision=5)}')
    st.caption('Transfer function assumes zero initial energy, unlike the time response, which includes your chosen initial state.')
    st.subheader('Pole movement when a component changes')
    adjustable=components(circuit)
    pole_param=st.selectbox('Change component',adjustable,index=0,key='poleparam')
    v0=p[pole_param]; values=np.linspace(max(v0*.20,.0001),v0*2.5,46)
    pm=pd.DataFrame(pole_sweep(circuit,p,pole_param,values))
    fp=go.Figure()
    for pole_id,segment in pm.groupby('pole_number'):
        fp.add_scatter(x=segment['real'],y=segment['imag'],mode='markers+lines',name=f'Pole {pole_id}',marker=dict(size=5,color=segment['parameter_value'],colorscale='Viridis',showscale=(pole_id==1),colorbar=dict(title=f'{pole_param} (SI)')))
    fp.add_vline(x=0,line_dash='dash',line_color='red')
    fp.update_layout(title=f'Root locus under {pole_param} variation (not loop-gain root locus)',xaxis_title='Real(s)',yaxis_title='Imag(s)',height=400)
    st.plotly_chart(fp,use_container_width=True)
    st.download_button('Download pole sweep CSV',pm.to_csv(index=False),f'{circuit}_pole_sweep.csv','text/csv')

# Coordinate system: C shown in mF to avoid a confusing 0.001-to-0.2 F label.
def to_ui(parameter,value): return value*1000 if parameter=='C' else value
def from_ui(parameter,value):return value/1000 if parameter=='C' else value
def param_label(parameter):return 'C (mF)' if parameter=='C' else (parameter+' (H)' if parameter=='L' else parameter+' (Ω)')

def range_controls(prefix,param):
    v=to_ui(param,p[param]); lo_default=max(v*.50, .001); hi_default=v*1.5
    return st.slider(f'{param_label(param)} variation (centered around current value)',min_value=.1,max_value=3.0,value=(.5,1.5),step=.1,key=f'{prefix}_{param}_range')

@st.cache_data(show_spinner=False,max_entries=12)
def cached_two(circuit,p_tuple,exc,initial,xname,xvals,yname,yvals,names,metric_name,at,window):
    cfg=dict(p_tuple)
    return two_parameter_surfaces(circuit,cfg,exc,initial,xname,np.array(xvals),yname,np.array(yvals),names,metric_name,at,window,180)

@st.cache_data(show_spinner=False,max_entries=12)
def cached_time(circuit,p_tuple,exc,initial,param,low,high,output,window):
    return time_surface(circuit,dict(p_tuple),exc,initial,param,low,high,output,window,220,17)

with surf_time_tab:
    st.subheader('3D response surface — time × one component parameter')
    st.write('Rotate this graph with the mouse. X = time, Y = component value, Z = a chosen element voltage or current. Every row is a separately simulated time response.')
    available=components(circuit)
    cc1,cc2=st.columns(2)
    with cc1:
        parameter=st.selectbox('Vary this component',available,key='timevary')
        chosen_out=st.selectbox('Measured voltage/current',list(output_defs),format_func=pretty,key='timeout')
    with cc2:
        fractions=range_controls('time',parameter)
    v=p[parameter]; low=v*fractions[0];high=v*fractions[1]
    try:
        with st.spinner('Calculating 17 circuit simulations...'):
            ts,axis,values=cached_time(circuit,tuple(p.items()),exc,tuple(x0),parameter,low,high,chosen_out,duration)
        display_axis=np.array([to_ui(parameter,k) for k in axis])
        fig=go.Figure(go.Surface(x=ts,y=display_axis,z=values,colorscale='Viridis',colorbar=dict(title=output_units(chosen_out))))
        fig.update_layout(height=630,title=f'{pretty(chosen_out)} against time and {param_label(parameter)}',scene=dict(xaxis_title='Time (s)',yaxis_title=param_label(parameter),zaxis_title=pretty(chosen_out)))
        st.plotly_chart(fig,use_container_width=True)
        st.download_button('Download interactive 3D graph (HTML)',fig.to_html(include_plotlyjs=True),f'{circuit}_time_3D.html','text/html',key='t3ddown')
    except (ValueError,RuntimeError) as e:st.warning(str(e))

with surf_two_tab:
    st.subheader('3D TWO-variable sweep: parameter X × parameter Y × output')
    st.write('Choose two independent component values (for example R and C or R and L). Each point on this 3D surface is calculated using the actual circuit model and chosen input. No assumed graphical shape.')
    available=components(circuit)
    if len(available)<2:
        st.info('Two different parameters are required for this analysis.')
    else:
        a,b=st.columns(2)
        with a: px=st.selectbox('X component',available,index=0,key='px')
        with b: py=st.selectbox('Y component',[k for k in available if k!=px],index=0,key='py')
        xx_factor=range_controls('x',px)
        yy_factor=range_controls('y',py)
        ngrid=st.slider('Number of values per axis',5,15,9,2)
        metric_name=st.selectbox('What does height (Z) mean?', ['Value at selected time','Peak absolute value','RMS over window','Peak-to-peak'])
        observation=st.slider('Observation time (s)',0.,float(duration),float(duration*.5),float(duration/100)) if metric_name=='Value at selected time' else duration*.5
        st.caption('Pick one, several, or ALL measured voltages/currents. Voltage surfaces are in V; current surfaces are in A.')
        outputs_choice=st.multiselect('Outputs for two-variable surfaces',list(output_defs),default=[list(output_defs)[0]],format_func=pretty,key='two_outs')
        if st.checkbox('Select ALL element outputs',False,key='all2'):outputs_choice=list(output_defs)
        xv=np.linspace(p[px]*xx_factor[0],p[px]*xx_factor[1],ngrid)
        yv=np.linspace(p[py]*yy_factor[0],p[py]*yy_factor[1],ngrid)
        if outputs_choice:
            try:
                with st.spinner(f'Calculating {ngrid*ngrid} simulations for {len(outputs_choice)} outputs...'):
                    surfaces=cached_two(circuit,tuple(p.items()),exc,tuple(x0),px,tuple(xv),py,tuple(yv),tuple(outputs_choice),metric_name,observation,duration)
                export_rows=[]
                for i,yy in enumerate(yv):
                    for j,xx in enumerate(xv):
                        row={param_label(px):to_ui(px,xx),param_label(py):to_ui(py,yy)}
                        row.update({pretty(n):float(surfaces[n][i,j]) for n in outputs_choice})
                        export_rows.append(row)
                for index,name in enumerate(outputs_choice):
                    graph=go.Figure(go.Surface(x=np.array([to_ui(px,v) for v in xv]),y=np.array([to_ui(py,v) for v in yv]),z=surfaces[name],colorscale='Viridis',colorbar=dict(title=output_units(name))))
                    graph.update_layout(title=f'{pretty(name)} — {metric_name}',height=500,scene=dict(xaxis_title=param_label(px),yaxis_title=param_label(py),zaxis_title=pretty(name)))
                    st.plotly_chart(graph,use_container_width=True,key='plot_2_'+name)
                    st.download_button('Download this interactive 3D graph (HTML)',graph.to_html(include_plotlyjs=True),f'{circuit}_{name}_3d_two_parameters.html','text/html',key='html_'+name)
                st.download_button('Download ALL selected 3D sweep data (CSV)',pd.DataFrame(export_rows).to_csv(index=False),file_name=f'{circuit}_two_variable_surface.csv',mime='text/csv')
            except (ValueError,RuntimeError) as e:st.warning(f'Sweep could not be completed: {e}')

with freq_tab:
    st.subheader('Frequency-response and sweeping phenomena')
    st.write('Steady-state sinusoidal response per 1 V peak AC input: |H(jω)| and phase. This frequency sweep is independent of the selected time-domain input and assumes zero initial conditions.')
    selected_freq=st.selectbox('Frequency-response output',list(output_defs),format_func=pretty,key='freqout')
    fstart,fstop=st.slider('Sweep frequency range (Hz)',min_value=.01,max_value=30.,value=(.05,10.),step=.01)
    grid=np.geomspace(fstart,fstop,150)
    H=frequency_response(circuit,p,selected_freq,grid)
    bode=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.12,subplot_titles=('Magnitude / input volt (dB re selected unit per V)','Phase (degrees)'))
    bode.add_scatter(x=grid,y=20*np.log10(np.maximum(np.abs(H),1e-14)),name='Magnitude (dB)',row=1,col=1)
    bode.add_scatter(x=grid,y=np.rad2deg(np.unwrap(np.angle(H))),name='Phase',row=2,col=1)
    bode.update_xaxes(type='log',title_text='Frequency (Hz)',row=2,col=1)
    bode.update_yaxes(title_text='Magnitude (dB)',row=1,col=1)
    bode.update_yaxes(title_text='Phase (°)',row=2,col=1)
    bode.update_layout(height=550)
    st.plotly_chart(bode,use_container_width=True)
    st.download_button('Download frequency-response CSV',pd.DataFrame({'Frequency (Hz)':grid,'Magnitude (selected output units/V)':np.abs(H),'Magnitude (dB)':20*np.log10(np.maximum(np.abs(H),1e-14)),'Phase (deg)':np.rad2deg(np.unwrap(np.angle(H)))}).to_csv(index=False),f'{circuit}_bode.csv','text/csv')
    st.subheader('3D frequency sweep against a component')
    freq_param=st.selectbox('Sweep component with frequency',components(circuit),key='freqparam')
    fracs=range_controls('freq',freq_param)
    vals=np.linspace(p[freq_param]*fracs[0],p[freq_param]*fracs[1],15)
    z=[]
    for v in vals:
        q=p.copy();q[freq_param]=float(v)
        h=frequency_response(circuit,q,selected_freq,grid)
        z.append(np.abs(h))
    z=np.asarray(z)
    fs=go.Figure(go.Surface(x=grid,y=np.array([to_ui(freq_param,v) for v in vals]),z=z,colorscale='Turbo',colorbar=dict(title=f'{output_units(selected_freq)}/V')))
    fs.update_layout(height=580,scene=dict(xaxis=dict(title='Frequency (Hz)',type='log'),yaxis_title=param_label(freq_param),zaxis_title='Magnitude (output units / input V)'),title='3D AC frequency response with parameter sweep')
    st.plotly_chart(fs,use_container_width=True)
    st.caption('Frequency sweeping and resonance effects are particularly informative for RLC models. A frequency chirp source is also available in the sidebar to examine transient swept-sine behavior.')

with export_tab:
    st.subheader('Export all results and reproduce your experiment')
    df=pd.DataFrame({'Time (s)':res.t,'Input voltage (V)':res.source})
    for i,stname in enumerate(states):df[stname.replace('_',' ').title()+' (state)']=res.states[i]
    for name,values in res.outputs.items():df[pretty(name)]=values
    st.dataframe(df.head(70),use_container_width=True,hide_index=True)
    st.download_button('Download ALL output voltages, currents, states (CSV)',df.to_csv(index=False),f'{circuit}_all_outputs.csv','text/csv')
    conf={'circuit':circuit,'parameters_SI':p,'waveform':exc.__dict__,'initial_conditions':dict(zip(states,x0)),'duration_s':duration,'samples':points,'poles':[{'real':float(l.real),'imag':float(l.imag)} for l in props['poles']]}
    st.download_button('Download configuration and poles (JSON)',json.dumps(conf,indent=2),f'{circuit}_settings.json','application/json')
    st.markdown('''**Sources & methods:** [SciPy signal and state-space](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ss2tf.html),
    [SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html),
    [Plotly 3D surface](https://plotly.com/python/3d-surface-plots/),
    [Streamlit charts](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart).
    Parallel topology includes source resistance Rs as a documented assumption. The project models ideal linear elements, not arbitrary nonlinear physical circuits.''')
