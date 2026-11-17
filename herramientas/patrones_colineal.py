import sys, json, os, time; sys.path.insert(0,'.')
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from antenas import tipos, simulacion
s = tipos.sustrato('FR4 JLC 1,6 mm')
casos=[('U recta','colineal_u_ref'),('Koch 1 (lin 1,08)','koch1_lin108'),('U recta plegada','plegada_recta')]
fig,ax=plt.subplots(2,3,figsize=(13,8),subplot_kw={'projection':'polar'})
for col,(t,et) in enumerate(casos):
    j=json.loads(open(f'salidas/_barridos/{et}/resultados.jsonl',encoding='utf-8').readline())
    a=tipos.generar('colineal_dipolos',j['parametros'])
    t0=time.time()
    r=simulacion.simular(a,s,2441.75e6,'normal',nf2ff=True,progreso=lambda m:None,paso=j['paso'],f_radiacion=2441.75e6)
    print(et,'simular',round(time.time()-t0),'s', r['direccion_max'], flush=True)
    th=np.array(r['theta']); ph=np.array(r['phi']); D=np.array(r['directividad_dBi_grid'])   # (theta, phi)
    # corte en el plano del eje (yz): phi = 90 y 270; corte ecuatorial (xy): theta = 90
    i90=np.argmin(abs(ph-90)); i270=np.argmin(abs(ph-270)); it90=np.argmin(abs(th-90))
    ang=np.concatenate([np.radians(th), -np.radians(th[::-1])])
    dd=np.concatenate([D[:,i90], D[::-1,i270]])
    ax[0,col].plot(ang,np.maximum(dd,-20)); ax[0,col].set_title(f'{t}\nplano del eje (yz)',fontsize=9)
    ax[1,col].plot(np.radians(ph),np.maximum(D[it90,:],-20)); ax[1,col].set_title('plano perpendicular al eje, θ=90° (xy)',fontsize=9)
    for a_ in ax[:,col]: a_.set_ylim(-20,max(8,D.max())); a_.set_theta_zero_location('N')
plt.tight_layout(); plt.savefig(r'salidas\_vistas\colineal_patrones.png',dpi=100); print('ok')
