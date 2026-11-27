"""Efecto de una carcasa de plástico sobre la hélice cuadrifilar (QHA): cuánto baja la resonancia y cuánto hay que acortar la tira.

Uso (desde la raíz):
    python herramientas/carcasa_helice.py [--f MHz] [--k 0.5847] [--etiqueta E] [--res 1.0] [--solo material|pared|holgura]

La carcasa es un tubo de plástico con base y tapa del mismo grosor alrededor de la hélice (modelo de `herramientas/helice_flex.py`: parámetros
`pared`, `holgura`, `er`, `tand`). Con D 32 mm y ¼ de vuelta barre el material (εr y tanδ de `antenas/carcasa.py` a la frecuencia), el grosor de la
pared y el hueco entre la tira y el tubo, simulando un solo puerto (~25 s cada caso), y da para cada uno la frecuencia de resonancia (X = 0), cuánto se
desplaza y el factor por el que hay que multiplicar el largo del brazo (`k`) para volver a centrarla (una iteración, primera aproximación).
Con malla de 1 mm el desplazamiento sale hasta 2–4 puntos mayor que con 0,6 mm (la pared de 1,2–1,6 mm cae entre líneas): usa `--res 0,6` para los números.
Resultado en `salidas/_barridos/<E>/carcasa.json`. Plásticos: valores típicos sin medir (`antenas/carcasa.MATERIALES`).
"""
import os
import sys
import json
import importlib.util
import tempfile
import hashlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)


def cargar_helice():
    spec = importlib.util.spec_from_file_location('helice_flex', os.path.join(RAIZ, 'herramientas', 'helice_flex.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def resonancia(hf, p, f_MHz, res=1.0):
    """(f de resonancia MHz o None, Z a f0) simulando solo el puerto 1."""
    import numpy as np
    h = hashlib.md5(json.dumps([p, f_MHz, res], sort_keys=True).encode()).hexdigest()[:10]
    s, _c, i0 = hf.simular_helice(p, f_MHz, res, os.path.join(tempfile.gettempdir(), 'antenas_sim', 'qha_' + h + '_A'), 1)
    z = s['Z']
    x = np.imag(z)
    cr = np.where((x[:-1] < 0) & (x[1:] >= 0))[0]
    return (float(s['f'][cr[0]])/1e6 if len(cr) else None), complex(z[i0])


def main():
    from antenas import carcasa
    hf = cargar_helice()
    opt, args, i = {}, sys.argv[1:], 0
    while i < len(args):
        opt[args[i][2:]] = args[i + 1]
        i += 2
    f_MHz = float(opt.get('f', '1575.42'))
    k0 = float(opt.get('k', '0.5847'))
    res = float(opt.get('res', '1.0'))
    solo = opt.get('solo')
    carpeta = os.path.join(RAIZ, 'salidas', '_barridos', opt.get('etiqueta', 'QHA_carcasa'))
    os.makedirs(carpeta, exist_ok=True)
    os.environ.setdefault('ANTENAS_GPU', '1')
    base = dict(hf.DEFECTOS, D=32.0, vueltas=0.25, k=k0, sentido=-1.0)

    def caso(nombre, **kw):
        q = dict(base, **kw)
        fr, z = resonancia(hf, q, f_MHz, res)
        fila = {'caso': nombre, **{k: kw[k] for k in kw}, 'f_resonancia_MHz': round(fr, 1) if fr else None,
                'desplazamiento_%': round(100*(fr/f_MHz - 1), 1) if fr else None,
                'Z_f0': [round(z.real, 1), round(z.imag, 1)],
                'factor_k_para_centrar': round(fr/f_MHz, 3) if fr else None}
        print(json.dumps(fila, ensure_ascii=False), flush=True)
        return fila

    filas = [caso('sin carcasa')]
    if solo in (None, 'material'):
        for mat in ('PLA', 'PETG', 'ABS', 'PA12', 'PA-GF'):
            er, tand = carcasa.propiedades({'material': mat}, f_MHz*1e6)
            filas.append(caso(f'material {mat}', pared=1.6, holgura=1.0, er=round(er, 3), tand=round(tand, 4)))
    er, tand = carcasa.propiedades({'material': 'PLA'}, f_MHz*1e6)
    pla = dict(er=round(er, 3), tand=round(tand, 4))
    if solo in (None, 'pared'):
        for pared in (0.8, 1.2, 2.4, 3.2):
            filas.append(caso(f'pared {pared} mm (PLA)', pared=pared, holgura=1.0, **pla))
    if solo in (None, 'holgura'):
        for hol in (0.2, 0.5, 2.0, 4.0, 8.0):
            filas.append(caso(f'holgura {hol} mm (PLA)', pared=1.6, holgura=hol, **pla))
    json.dump({'f_MHz': f_MHz, 'res_mm': res, 'D': 32.0, 'vueltas': 0.25, 'k': k0, 'filas': filas}, open(os.path.join(carpeta, 'carcasa.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print('TERMINADO ->', carpeta)


if __name__ == '__main__':
    main()
