"""Draw textbook-style topology schematics for the six models in Matplotlib."""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle, Arc


def circuit_diagram(kind, connection):
    components = list(kind) if kind != 'RLC' else ['R', 'L', 'C']
    fig, ax = plt.subplots(figsize=(9, 3.25))
    ax.set_aspect('equal')
    ax.set_xlim(-0.8, 10.6)
    ax.set_ylim(-0.8, 4.7)
    ax.axis('off')
    col = '#1d516b'
    def wire(x1, y1, x2, y2): ax.plot([x1,x2], [y1,y2], lw=2.0, color=col)
    def source(x, y):
        ax.add_patch(Circle((x,y), .42, fill=False, lw=2, ec=col))
        ax.text(x, y, '~', ha='center', va='center', fontsize=18, color=col)
        ax.text(x-.7, y, '$u(t)$', fontsize=13, ha='right', va='center', color=col)
    def part(label, x, y, horizontal=True):
        if label == 'R' or label == 'Rs':
            if horizontal: ax.add_patch(Rectangle((x-.34,y-.19), .68,.38, lw=2,ec=col,fc='white'))
            else: ax.add_patch(Rectangle((x-.19,y-.34),.38,.68,lw=2,ec=col,fc='white'))
        elif label == 'C':
            if horizontal:
                wire(x-.12,y-.35,x-.12,y+.35); wire(x+.12,y-.35,x+.12,y+.35)
            else:
                wire(x-.36,y-.12,x+.36,y-.12); wire(x-.36,y+.12,x+.36,y+.12)
        else:
            if horizontal:
                for k in range(4): ax.add_patch(Arc((x-.25+k*.17,y),.25,.35,theta1=0,theta2=180,ec=col,lw=2))
            else:
                for k in range(4): ax.add_patch(Arc((x,y-.26+k*.17),.35,.25,theta1=270,theta2=90,ec=col,lw=2))
        dx,dy=(0,.60) if horizontal else (.61,0)
        ax.text(x+dx,y+dy,label if label != 'Rs' else '$R_s$',ha='center',va='center',fontsize=14,color=col)
    ytop, ybot = 3.6, .35
    source(1, (ytop+ybot)/2)
    wire(1,ytop,1,2.4);wire(1,1.55,1,ybot)
    if connection == 'Series':
        xs=np.linspace(3,8.1,len(components));wire(1,ytop,9,ytop);wire(9,ytop,9,ybot);wire(9,ybot,1,ybot)
        for x,lbl in zip(xs,components):
            ax.plot([x-.42,x+.42],[ytop,ytop],lw=4.8,color='white',zorder=3)
            part(lbl,x,ytop)
        ax.annotate('$i(t)$',xy=(5.8,4.01),fontsize=12,color=col)
    else:
        wire(1,ytop,9.7,ytop);wire(9.7,ytop,9.7,ybot);wire(9.7,ybot,1,ybot)
        ax.plot([2.1,3.05],[ytop,ytop],lw=4.8,color='white',zorder=3);part('Rs',2.55,ytop)
        branches=np.linspace(4.2,8.9,len(components))
        for x,lbl in zip(branches,components):
            wire(x,ytop,x,ybot)
            ax.plot([x,x],[(ytop+ybot)/2-.45,(ytop+ybot)/2+.45],lw=4.8,color='white',zorder=3)
            part(lbl,x,(ytop+ybot)/2,horizontal=False)
        ax.text(9.75,4.03,'$v(t)$',fontsize=13,color=col,ha='right')
    fig.tight_layout(pad=.5)
    return fig
