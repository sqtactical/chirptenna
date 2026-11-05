"""Construye la versión web lite (GitHub Pages) en una carpeta: la interfaz de `web/` + el núcleo de `antenas/`.

El núcleo va empaquetado en `py/antenas.zip`, que el motor (Pyodide, en el navegador) descomprime e importa.
Solo lleva lo que funciona en el navegador: nada de openEMS, NanoVNA, NiceGUI ni KiCad.

Uso (desde la raíz):  python herramientas/construir_web.py [carpeta_salida]   (por defecto salidas/web)
Para probarla en local:  python -m http.server 8095 --directory salidas/web   ->   http://localhost:8095
"""
import os
import sys
import json
import shutil
import zipfile
import importlib.util

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Módulos del núcleo que usa la web (si un tipo nuevo necesita otro módulo, añadirlo aquí)
NUCLEO = ['__init__', 'ajuste', 'ancho_banda', 'conector', 'consejos', 'dipolos', 'directivas', 'exportar',
          'fabricacion', 'geometria', 'jpole', 'logo', 'materiales', 'modelo', 'presentacion', 'problemas', 'robusto',
          'tipos', 'tipos_base', 'web_api']
DATOS = ['calibracion_estimaciones.json', 'logo_texto.json']
# Lo que el núcleo no puede importar en el navegador
PROHIBIDOS = ('CSXCAD', 'openEMS', 'serial', 'nicegui', 'matplotlib', 'plotly', 'h5py', 'gerbonara')


def comprobar_nucleo():
    """Falla si algún módulo del núcleo importa (al cargarse) algo que no existe en el navegador."""
    sys.path.insert(0, RAIZ)
    antes = set(sys.modules)
    import antenas.web_api  # noqa: F401
    nuevos = set(sys.modules) - antes
    malos = sorted({m.split('.')[0] for m in nuevos} & set(PROHIBIDOS))
    if malos:
        raise SystemExit(f'El núcleo importa módulos que no hay en el navegador: {", ".join(malos)}')
    faltan = [m for m in nuevos if m.startswith('antenas.') and m.split('.')[1] not in NUCLEO]
    if faltan:
        raise SystemExit(f'El núcleo usa módulos que no están en NUCLEO: {", ".join(sorted(faltan))}')


def main():
    salida = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'salidas', 'web'))
    comprobar_nucleo()
    if os.path.isdir(salida):
        shutil.rmtree(salida)
    shutil.copytree(os.path.join(RAIZ, 'web'), salida)
    shutil.copy2(os.path.join(RAIZ, 'docs', 'logo', 'chirptenna.png'), os.path.join(salida, 'logo.png'))
    os.makedirs(os.path.join(salida, 'py'))
    with zipfile.ZipFile(os.path.join(salida, 'py', 'antenas.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for m in NUCLEO:
            z.write(os.path.join(RAIZ, 'antenas', m + '.py'), f'antenas/{m}.py')
        for d in DATOS:
            z.write(os.path.join(RAIZ, 'antenas', d), f'antenas/{d}')
    spec = importlib.util.spec_from_file_location('ver', os.path.join(RAIZ, 'antenas', '__init__.py'))
    ver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ver)
    with open(os.path.join(salida, 'version.json'), 'w', encoding='utf-8') as fh:
        json.dump({'version': ver.__version__}, fh)
    # GitHub Pages: sin Jekyll (no ignora carpetas ni procesa nada)
    open(os.path.join(salida, '.nojekyll'), 'w').close()
    tam = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(salida) for f in fs)
    print(f'Web lite v{ver.__version__} en {salida} ({tam//1024} kB)')


if __name__ == '__main__':
    main()
