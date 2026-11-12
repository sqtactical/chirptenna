"""Herramienta de idiomas de la interfaz (ver `antenas/i18n.py`).

Uso (desde la raíz):
    python herramientas/i18n.py extraer             # cuenta los textos traducibles del código
    python herramientas/i18n.py faltan [codigo]     # textos sin traducir (todos los idiomas si no se da código); código 1 si faltan
    python herramientas/i18n.py actualizar codigo   # añade al fichero del idioma las claves nuevas (con valor vacío) y avisa de las que sobran
    python herramientas/i18n.py limpiar codigo      # quita del fichero las claves que ya no están en el código
    python herramientas/i18n.py nuevo codigo "Nombre"   # crea idioma/<codigo>.json con todas las claves vacías

Los textos fuente están en castellano y son la clave. Se extraen:
  · el primer argumento literal de `tr(...)` y `N_(...)` en gui/ y antenas/;
  · todos los textos de interfaz de los módulos de datos (DATOS: nombres de tipo, etiquetas, ayudas, avisos…),
    que se traducen al mostrarlos.
Un texto con valor vacío en el fichero del idioma cuenta como sin traducir (se muestra en castellano).
"""
import os
import re
import sys
import ast
import json

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
DIR_IDIOMAS = os.path.join(RAIZ, 'antenas', 'idiomas')
CARPETAS = [os.path.join(RAIZ, 'gui'), os.path.join(RAIZ, 'antenas')]
# Módulos con textos de interfaz escritos como datos (no dentro de tr)
DATOS = ['guia', 'tipos', 'problemas', 'presentacion', 'consejos', 'ajuste', 'materiales', 'miniaturas', 'conector',
         'fabricacion', 'integracion', 'web_api']
# Textos que parecen de interfaz pero no lo son (claves internas, identificadores…)
IGNORAR = {'Chirptenna', 'DejaVu Sans', 'F.Cu', 'B.Cu', 'GND', 'ANT', 'Antenas.pretty/', 'texto {0}'}
# Textos cortos que el filtro descartaría (se muestran en la interfaz sin pasar por tr)
EXTRA = {'Otra', 'vivo', 'malla'}
# Mensajes solo para quien desarrolla (comprobaciones de guia.py) y trozos de plantillas no traducibles
IGNORAR_CONTIENE = ('guia.TIPOS', 'preserveAspectRatio', ': el básico «', ': el parámetro «', '» no es un parámetro', '» no tiene ayuda', 'consejos(antena', 'problemas(clave')

_CSS = re.compile(r"[a-z0-9_\-:/\[\]\.\(\)%#,=;!\s'\"@*+>&|<~?^{}$\\]+")


def es_texto(s):
    """¿Parece un texto para el usuario? (descarta identificadores, clases CSS, rutas…)"""
    if re.fullmatch(r'[A-Za-z0-9]+(_[A-Za-z0-9]+)+', s) or any(x in s for x in IGNORAR_CONTIENE):
        return False
    if '%{' in s or re.fullmatch(r'[A-Z0-9_\.]+', s) or re.fullmatch(r'[A-Za-z]\w*\.[A-Za-z]\w*', s) or len(s.strip()) <= 4:
        return False
    if not re.search(r'[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]{2,}', s):
        return False
    if _CSS.fullmatch(s) and not re.search(r'[A-Z]', s):
        return False
    return not s.startswith(('http', '/', '#', '<', '.'))


def _es_llamada_tr(n):
    return isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ('tr', 'N_')


def textos_de_fichero(ruta, todos):
    """Textos de un fichero: los de tr()/N_() y, si `todos`, también cualquier cadena que parezca de interfaz."""
    with open(ruta, encoding='utf-8') as fh:
        arbol = ast.parse(fh.read())
    hallados = set()
    docs = set()
    for n in ast.walk(arbol):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body and \
                isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            docs.add(id(n.body[0].value))
    for n in ast.walk(arbol):
        if _es_llamada_tr(n) and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            hallados.add(n.args[0].value)
        elif todos and isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs \
                and es_texto(n.value):
            hallados.add(n.value)
    return hallados


def textos_web():
    """Textos de la web lite: T('…') y N_('…') de web/app.js y los elementos con data-t de web/index.html."""
    out = set()
    ruta_js = os.path.join(RAIZ, 'web', 'app.js')
    if os.path.exists(ruta_js):
        js = open(ruta_js, encoding='utf-8').read()
        for m in re.finditer(r"\b(?:T|N_)\(\s*(?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\")", js):
            s = m.group(1) if m.group(1) is not None else m.group(2)
            out.add(s.replace("\\'", "'").replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\'))
    ruta_html = os.path.join(RAIZ, 'web', 'index.html')
    if os.path.exists(ruta_html):
        html = open(ruta_html, encoding='utf-8').read()
        attrs = r"((?:[^>'\"]|\"[^\"]*\"|'[^']*')*)"
        for m in re.finditer(r'<(\w+)\b' + attrs + r'>', html):      # etiquetas de apertura (con data-t, sin anidar)
            a_ = m.group(2)
            v = re.search(r"\bdata-t(?:=(?:'([^']*)'|\"([^\"]*)\"))?(?=\s|$)", a_)
            if not v:
                continue
            cierre = html.find(f'</{m.group(1)}>', m.end())
            interior = html[m.end():cierre] if cierre >= 0 else ''
            clave = v.group(1) or v.group(2) or re.sub(r'\s+', ' ', interior).strip()
            if clave:
                out.add(clave)
    return out


def extraer():
    """Conjunto de todos los textos traducibles del código."""
    out = set()
    for carpeta in CARPETAS:
        for nombre in sorted(os.listdir(carpeta)):
            if nombre.endswith('.py') and nombre != 'i18n.py':
                out |= textos_de_fichero(os.path.join(carpeta, nombre), nombre[:-3] in DATOS and carpeta.endswith('antenas'))
    out |= textos_web()
    return {t for t in out | EXTRA if t not in IGNORAR}


def ruta_idioma(codigo):
    return os.path.join(DIR_IDIOMAS, f'{codigo}.json')


def cargar(codigo):
    with open(ruta_idioma(codigo), encoding='utf-8-sig') as fh:
        return json.load(fh)


def guardar(codigo, datos):
    os.makedirs(DIR_IDIOMAS, exist_ok=True)
    datos['textos'] = dict(sorted(datos['textos'].items()))
    with open(ruta_idioma(codigo), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=1)
        fh.write('\n')


def codigos():
    if not os.path.isdir(DIR_IDIOMAS):
        return []
    return sorted(f[:-5] for f in os.listdir(DIR_IDIOMAS) if f.endswith('.json'))


def faltan(codigo, textos):
    datos = cargar(codigo)['textos']
    return sorted(t for t in textos if not datos.get(t))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'extraer'
    textos = extraer()
    if cmd == 'extraer':
        print(f'{len(textos)} textos traducibles; idiomas: {", ".join(codigos()) or "(ninguno)"}')
    elif cmd == 'faltan':
        lista = sys.argv[2:] or codigos()
        mal = 0
        for c in lista:
            f = faltan(c, textos)
            sobran = sorted(t for t in cargar(c)['textos'] if t not in textos)
            print(f'{c}: {len(textos) - len(f)}/{len(textos)} traducidos; {len(f)} sin traducir; {len(sobran)} que ya no se usan')
            for t in f[:40]:
                print('   falta:', t[:110].replace('\n', ' '))
            if len(f) > 40:
                print(f'   … y {len(f) - 40} más')
            mal += bool(f)
        sys.exit(1 if mal else 0)
    elif cmd == 'actualizar':
        c = sys.argv[2]
        datos = cargar(c)
        nuevos = [t for t in textos if t not in datos['textos']]
        for t in nuevos:
            datos['textos'][t] = ''
        sobran = [t for t in datos['textos'] if t not in textos]
        guardar(c, datos)
        print(f'{c}: {len(nuevos)} claves nuevas (vacías); {len(sobran)} ya no se usan (no se borran)')
    elif cmd == 'limpiar':
        c = sys.argv[2]
        datos = cargar(c)
        sobran = [t for t in datos['textos'] if t not in textos]
        for t in sobran:
            del datos['textos'][t]
        guardar(c, datos)
        print(f'{c}: quitadas {len(sobran)} claves que ya no se usan')
    elif cmd == 'nuevo':
        c, nombre = sys.argv[2], sys.argv[3]
        if os.path.exists(ruta_idioma(c)):
            sys.exit(f'{c} ya existe')
        guardar(c, {'_nombre': nombre, 'textos': {t: '' for t in textos}})
        print(f'creado {ruta_idioma(c)} con {len(textos)} textos por traducir')
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
