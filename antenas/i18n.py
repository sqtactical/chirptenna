"""Idiomas de la interfaz (i18n). El texto fuente está en castellano y sirve de clave (como gettext).

    from antenas.i18n import tr
    tr('Guardar')                       -> 'Save' si el idioma es el inglés
    tr('Banda {0} MHz', 2441.75)        -> formatea con str.format tras traducir
    tr('Banda {f} MHz', f=2441.75)

Un idioma es un fichero `antenas/idiomas/<código>.json`:
    {"_nombre": "English", "textos": {"Guardar": "Save", ...}}
El castellano (`es`) es la fuente: no tiene fichero. **Para añadir un idioma, copiar `en.json` con el código
nuevo (`fr.json`), poner `_nombre` y traducir los valores**; aparece solo en el selector. Un texto sin
traducir se muestra en castellano (nunca falla). `herramientas/i18n.py` lista lo que falta.

El idioma actual es global del proceso (la interfaz es de un solo usuario en local).
"""
import os
import re
import json
import unicodedata

IDIOMA_BASE = 'es'
NOMBRE_BASE = 'Castellano'
DIR_IDIOMAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'idiomas')

_actual = IDIOMA_BASE
_catalogos = {}     # código -> {texto en castellano: traducción}
_nombres = {}       # código -> nombre del idioma en su propia lengua
_cargado = False

# Easter egg: el «idioma LoRa». No tiene fichero: cada letra se convierte en un trazo de chirrido (/ sube, \\ baja,
# _ se mantiene) y se conservan los números, la puntuación, las unidades y las marcas {0}, {x:.1f} y <br>.
# No sale en el selector (se activa con ?idioma=lora, CHIRPTENNA_IDIOMA=lora o pinchando 5 veces el grillo).
IDIOMA_LORA = 'lora'
NOMBRE_LORA = '/\\_/\\\\/ LoRa'
_TROZOS = re.compile(r'\{[^}]*\}|<[^>]*>|[^\W\d_]+')


def chirp(texto):
    """Texto en «LoRa»: letras a trazos de chirrido, sin tocar lo que no es una palabra (ni sus marcas de formato)."""
    def trozo(m):
        t = m.group(0)
        if t[0] in '{<':
            return t
        base = (unicodedata.normalize('NFD', c)[0].lower() for c in t)
        return ''.join('/_\\'[(ord(c) - 97) % 3 if 'a' <= c <= 'z' else 1] for c in base)
    return _TROZOS.sub(trozo, texto)


def _cargar():
    global _cargado
    if _cargado:
        return
    _cargado = True
    _nombres[IDIOMA_BASE] = NOMBRE_BASE
    _nombres[IDIOMA_LORA] = NOMBRE_LORA
    if not os.path.isdir(DIR_IDIOMAS):
        return
    for nombre in sorted(os.listdir(DIR_IDIOMAS)):
        if not nombre.endswith('.json'):
            continue
        codigo = nombre[:-5]
        try:
            with open(os.path.join(DIR_IDIOMAS, nombre), encoding='utf-8-sig') as fh:
                datos = json.load(fh)
        except (OSError, ValueError):
            continue
        _catalogos[codigo] = datos.get('textos', {})
        _nombres[codigo] = datos.get('_nombre', codigo)


def idiomas():
    """{código: nombre propio} de los idiomas del selector (el castellano primero; «LoRa» solo si es el actual)."""
    _cargar()
    visibles = {c: n for c, n in _nombres.items() if c not in (IDIOMA_BASE, IDIOMA_LORA) or c == _actual}
    return {IDIOMA_BASE: _nombres[IDIOMA_BASE], **{c: n for c, n in visibles.items() if c != IDIOMA_BASE}}


def catalogo(codigo):
    """Diccionario {castellano: traducción} de un idioma (vacío para el castellano o uno desconocido)."""
    _cargar()
    return _catalogos.get(codigo, {})


def idioma():
    return _actual


def fijar_idioma(codigo):
    """Cambia el idioma actual; un código desconocido deja el castellano. Devuelve el código aplicado."""
    global _actual
    _cargar()
    _actual = codigo if codigo in _nombres else IDIOMA_BASE
    return _actual


def idioma_inicial(preferido=None):
    """Idioma con el que arrancar: el guardado, si no la variable CHIRPTENNA_IDIOMA, si no el castellano."""
    _cargar()
    for c in (preferido, os.environ.get('CHIRPTENNA_IDIOMA')):
        if c and c in _nombres:
            return c
    return IDIOMA_BASE


def tr(texto, *args, **kw):
    """Traduce `texto` (en castellano) al idioma actual y, si se pasan argumentos, lo formatea con `str.format`."""
    _cargar()
    if _actual == IDIOMA_LORA:
        texto = chirp(texto)
    elif _actual != IDIOMA_BASE:
        texto = _catalogos.get(_actual, {}).get(texto) or texto
    return texto.format(*args, **kw) if (args or kw) else texto


def N_(texto):
    """Marca un texto para extraerlo sin traducirlo aún (datos que se traducen al mostrarlos con `tr`)."""
    return texto
