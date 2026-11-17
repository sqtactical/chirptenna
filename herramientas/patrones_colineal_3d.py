import sys, json, time; sys.path.insert(0,'.')
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from antenas import tipos, simulacion, geometria as g
s = tipos.sustrato('FR4 JLC 1,6 mm')
casos=[('U recta (301 mm)','colineal_u_ref'),('U recta plegada (216 mm)','plegada_recta'),('U de Koch plegada (194 mm)','plegada_koch')]
fig=plt.figure(figsize=(17,7))
for k,(t,et) in enumerate(casos):
    j=json.loads(open(f'salidas/_barridos/{et}/resultados.jsonl',encoding='utf-8').readline())
    a=tipos.generar('colineal_dipolos',j['parametros'])
    r=simulacion.simular(a,s,2441.75e6,'normal',nf2ff=True,progreso=lambda m:None,paso=j['paso'],f_radiacion=2441.75e6)
    th=np.radians(r['theta']); ph=np.radians(r['phi']); D=np.array(r['directividad_dBi_grid'])
    P,T=np.meshgrid(ph,th)
    rad=np.maximum(D+20,0)/26*90                  # mm: 90 mm = máximo (+6 dBi), 0 = −20 dBi
    X=rad*np.sin(T)*np.cos(P); Y=rad*np.sin(T)*np.sin(P); Z=rad*np.cos(T)
    x0,y0,x1,y1=a.contorno.bounds; cx,cy=(x0+x1)/2,(y0+y1)/2
    ax=fig.add_subplot(1,3,k+1,projection='3d')
    ax.plot_surface(X,Y,Z,facecolors=cm.viridis(colors.Normalize(-10,6)(D)),rstride=1,cstride=1,linewidth=0,antialiased=True,alpha=0.55,shade=False)
    for cap,col in (('B.Cu','#4a6fa5'),('F.Cu','#c98a2b')):
        for pol in g.poligonos(a.capas[cap]):
            xx,yy=pol.exterior.xy
            ax.add_collection3d(Poly3DCollection([[(x-cx,y-cy,0.0) for x,y in zip(xx,yy)]],facecolor=col,edgecolor=col,alpha=1.0))
    ax.set_box_aspect((1,1,1)); L=max(110,(y1-y0)/2+10)
    ax.set_xlim(-L,L); ax.set_ylim(-L,L); ax.set_zlim(-L,L); ax.view_init(elev=22,azim=-60)
    ax.set_title(f"{t}\nD {D.max():.1f} dBi · máx θ {r['direccion_max']['theta']:.0f}° φ {r['direccion_max']['phi']:.0f}°",fontsize=10)
    ax.set_xlabel('x'); ax.set_ylabel('y (eje de la antena)'); ax.set_zlabel('z (normal a la placa)')
    print(et,'ok',flush=True)
plt.tight_layout(); plt.savefig(r'salidas\_vistas\colineal_patrones_3d.png',dpi=95); print('listo')
