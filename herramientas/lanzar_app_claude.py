"""Arranca gui/app.py deshaciendo la virtualización de rutas de la app de Claude (lección 49 de CLAUDE.md):
Path.resolve() de un archivo del venv da ...\\Packages\\Claude_*\\LocalCache\\Local\\..., la de su carpeta no, y NiceGUI da 403
a Plotly. Solo hace falta en la sesión de Claude; en el ordenador del usuario se lanza gui/app.py directamente.

    python herramientas/lanzar_app_claude.py [argumentos de gui/app.py]        (desde la raíz del proyecto)
    python herramientas/capturas_readme.py --lanzador herramientas/lanzar_app_claude.py
"""
import os
import pathlib
import re
import runpy
import sys

_LOCAL = os.environ['LOCALAPPDATA']
_PATRON = re.compile(re.escape(_LOCAL) + r'\\Packages\\Claude_[^\\]+\\LocalCache\\Local', re.IGNORECASE)
_original = pathlib.Path.resolve


def _resolve(self, strict=False):
    r = _original(self, strict=strict)
    s = _PATRON.sub(lambda m: _LOCAL, str(r))
    return type(r)(s) if s != str(r) else r


pathlib.Path.resolve = _resolve
app = os.path.join(os.getcwd(), 'gui', 'app.py')
sys.argv = [app] + sys.argv[1:]
runpy.run_path(app, run_name='__main__')
