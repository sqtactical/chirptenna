"""API de la versión web lite (diseñar, ver y exportar para KiCad), pensada para Pyodide en el navegador.

Todo entra y sale como JSON (o bytes en la exportación) para que la interfaz web (`web/`) no dependa de
cómo están hechos los módulos. Usa solo el núcleo del paquete: nada de openEMS, NanoVNA, NiceGUI ni KiCad.
`VERSION_API` sube si cambia el formato de entrada o de salida.

Uso desde JavaScript (motor.js): `api.catalogo()`, `api.dimensionar(json)`, `api.generar(json)`,
`api.exportar(json)`; cada una recibe y devuelve una cadena JSON salvo `exportar`, que devuelve bytes (zip).
"""
import io
import os
import sys
import json
import time
import zipfile
import tempfile

if sys.platform == 'emscripten':          # navegador (Pyodide): GEOS 3.12, operaciones con rejilla robusta
    from . import robusto
    robusto.activar()

from . import tipos, fabricacion, consejos, problemas, presentacion, guia, exportar as exp, __version__
from . import i18n
from .i18n import tr
from .geometria import poligonos
from .materiales import SUSTRATOS, SUSTRATO_POR_DEFECTO

VERSION_API = 2          # 2: galería (grupo, resumen, estado), parámetros básicos y ayudas
URL_PROYECTO = 'https://github.com/sqtactical/chirptenna'


def nombre_valido(nombre):
    """Igual que `biblioteca.nombre_valido` (no se importa: biblioteca usa rutas de Windows)."""
    limpio = ''.join(c if (c.isalnum() or c in '-_.') else '_' for c in (nombre or '').strip())
    return limpio.strip('._') or 'antena'


def _r(v):
    return round(float(v), 3)


def _anillos(geom):
    """[[exterior, hueco, …], …] con coordenadas redondeadas a 1 µm (para dibujar con relleno par-impar)."""
    out = []
    for p in poligonos(geom):
        out.append([[[_r(x), _r(y)] for x, y in p.exterior.coords]] +
                   [[[_r(x), _r(y)] for x, y in h.coords] for h in p.interiors])
    return out


def _json(datos):
    return json.dumps(datos, ensure_ascii=False, default=float)


def catalogo():
    """Tipos con sus parámetros, sustratos, reglas, bandas y textos de la serigrafía."""
    lista = []
    for clave, t in tipos.CATALOGO.items():
        grupo, resumen, _ = guia.info_tipo(clave)
        est, comentario = problemas.estado(clave)
        lista.append({
            'clave': clave, 'nombre': t.nombre, 'descripcion': t.descripcion, 'familia': t.familia,
            'grupo': grupo, 'resumen': resumen, 'estado': est, 'estado_comentario': comentario,
            'parametros': [{'nombre': p.nombre, 'etiqueta': p.etiqueta, 'defecto': p.defecto, 'minimo': p.minimo,
                            'maximo': p.maximo, 'paso': p.paso, 'entero': p.entero, 'ayuda': guia.ayuda(clave, p),
                            'opciones': ({str(k): v for k, v in p.opciones.items()} if p.opciones else None)}
                           for p in t.parametros],
            'escalables': list(tipos.ESCALABLES.get(clave, ())),
        })
    return _json({
        'version': __version__, 'version_api': VERSION_API, 'url': URL_PROYECTO,
        'tipos': lista, 'grupos': guia.GRUPOS, 'estados': problemas.ESTADO_TEXTO, 'sustratos': list(SUSTRATOS), 'sustrato_defecto': SUSTRATO_POR_DEFECTO,
        'reglas': list(fabricacion.REGLAS), 'reglas_defecto': fabricacion.REGLAS_POR_DEFECTO,
        'bandas': presentacion.BANDAS,
        'serigrafia_opciones': [o for o in presentacion.SERIGRAFIA_OPCIONES if o[0] != 'sim'],   # sin simulación
        'serigrafia_defecto': {k: v for k, v in presentacion.SERIGRAFIA_DEFECTO.items() if k != 'sim'},
        'logo_opciones': presentacion.LOGO_OPCIONES, 'aviso_sin_logo': presentacion.AVISO_SIN_LOGO,
        'aviso_general': problemas.AVISO_GENERAL,
    })


def _entrada(texto):
    e = json.loads(texto)
    i18n.fijar_idioma(e.get('idioma') or i18n.IDIOMA_BASE)      # idioma de los textos que genera Python
    clave = e['clave']
    p = tipos.CATALOGO[clave].defectos()
    p.update(e.get('parametros') or {})
    return e, clave, p


def dimensionar(texto):
    """Ajusta el tamaño a la frecuencia (o amplía la banda si `ampliar_banda`). Devuelve parámetros y aviso."""
    e, clave, p = _entrada(texto)
    if e.get('ampliar_banda'):
        p, aviso = tipos.ajustar_ancho_banda(clave, e['f_MHz']*1e6, e['bw_MHz']*1e6, p, e.get('sustrato'))
    else:
        p = tipos.dimensionar(clave, e['f_MHz']*1e6, p, e.get('sustrato'))
        aviso = p.pop('_aviso', '')
    p.pop('_aviso', None)
    return _json({'parametros': p, 'aviso': aviso})


def _vista(a):
    """Geometría para dibujar la antena (capas, contorno, taladros, componentes, marcas y conector)."""
    aj = a.ajuste or {}
    taladros = [[_r(x), _r(y), _r(d)] for x, y, d in a.taladros]
    if a.puerto.get('tipo') == 'pasante':
        taladros.append([*map(_r, a.puerto['alimentacion']), _r(a.puerto['taladro_mm'])])
    pads = []
    for c in aj.get('componentes', []):
        r = int(round(c['rot']/90.0)) % 4
        for dx, dy, w, h in c['pads']:
            rx, ry = [(dx, dy), (-dy, dx), (-dx, -dy), (dy, -dx)][r]
            sw, sh = (h, w) if r % 2 else (w, h)
            pads.append([_r(c['x'] + rx - sw/2), _r(c['y'] + ry - sh/2), _r(sw), _r(sh)])
    ipex = []
    if a.puerto.get('conector') == 1:
        from .conector import pads_ipex
        for _, (x, y), (sx, sy) in pads_ipex(a.puerto)[0]:
            ipex.append([_r(x - sx/2), _r(y - sy/2), _r(sx), _r(sy)])
    return {
        'contorno': [[[_r(x), _r(y)] for x, y in anillo.coords]
                     for anillo in [a.contorno.exterior] + list(a.contorno.interiors)],
        'cobre_sup': _anillos(a.cobre('F.Cu')),
        'cobre_inf': _anillos(a.cobre('B.Cu')),
        'reflector': ([[_r(x), _r(y)] for x, y in a.reflector['contorno'].exterior.coords]
                      if a.reflector else None),
        'separacion_reflector_mm': (_r(a.reflector['separacion_mm']) if a.reflector else None),
        'taladros': taladros,
        'componentes': [{'ref': c['ref'], 'valor': c['valor'], 'x': _r(c['x']), 'y': _r(c['y'])}
                        for c in aj.get('componentes', [])],
        'pads': pads,
        'marcas': [{'linea': [[_r(x), _r(y)] for x, y in m['linea']], 'texto': m['texto'],
                    'pos': [_r(m['pos'][0]), _r(m['pos'][1])]} for m in aj.get('marcas', [])],
        'puerto': [_r(a.puerto['borde'][0]), _r(a.puerto['borde'][1])],
        'tipo_puerto': a.puerto.get('tipo', ''),
        'conector': 'IPEX' if a.puerto.get('conector') == 1 else 'SMA',
        'ipex': ipex,
    }


def generar(texto):
    """Genera la antena y devuelve vista, resultados, consejos, comprobaciones y problemas conocidos."""
    e, clave, p = _entrada(texto)
    f_MHz, bw_MHz = float(e['f_MHz']), float(e['bw_MHz'])
    lo, hi = f_MHz - bw_MHz/2, f_MHz + bw_MHz/2
    try:
        a = tipos.generar(clave, p, e.get('sustrato'))
    except Exception as ex:      # geometría imposible con estos parámetros
        return _json({'error': tr('No se puede generar: {0}', ex), 'visibles': presentacion.parametros_visibles(clave, p),
                      'basicos': guia.basicos(clave, p)})
    bw = a.info.get('ancho_banda_estimado')
    banda = None
    if bw:
        cubre = bw['f_inf_MHz'] <= lo and bw['f_sup_MHz'] >= hi
        banda = {'texto': tr('Banda estimada {0:g}–{1:g} MHz ({2:g} MHz, {3:g} %) · necesaria {4:g}–{5:g} MHz',
                             bw['f_inf_MHz'], bw['f_sup_MHz'], bw['MHz'], bw['porcentaje'], lo, hi),
                 'estado': 'holgado' if cubre and bw['MHz'] >= 1.5*(hi - lo) else ('justo' if cubre else 'no')}
    comprobaciones = (fabricacion.comprobar(a, e.get('reglas') or fabricacion.REGLAS_POR_DEFECTO)
                      + [('aviso', m) for m in a.info.get('avisos', [])]
                      + [('info', m) for m in (a.info.get('ajuste') or [])])
    s = e.get('serigrafia') or presentacion.SERIGRAFIA_DEFECTO
    return _json({
        'vista': _vista(a),
        'info': [(tr(k), v) for k, v in presentacion.filas_info(a.info)],
        'banda': banda,
        'consejos': [(c, tr(t)) for c, t in consejos.consejos(a, f_MHz*1e6, (lo*1e6, hi*1e6))],
        'problemas': [(n, tr(t)) for n, t in problemas.problemas(clave, p, f_MHz)],
        'comprobaciones': [(n, tr(m)) for n, m in comprobaciones],
        'visibles': presentacion.parametros_visibles(clave, p),
        'basicos': guia.basicos(clave, p),
        'serigrafia': presentacion.lineas_serigrafia(s, clave, f_MHz, e.get('nombre', '')),
        'descripcion': tr(tipos.CATALOGO[clave].descripcion),
    })


LEEME = """Chirptenna {version} · {nombre}
{titulo}

Archivos
  {nombre}.kicad_pcb        Placa de prueba completa (antena, línea de 50 Ω, masa y conector). KiCad 8 o posterior.
  Antenas.pretty/{nombre}.kicad_mod   Solo la antena, para meterla en tu propia placa.
{extra}  diseno.json            El diseño: se abre en la web («Abrir diseño») o en «Mis diseños» de la aplicación.

Antes de fabricar (la web no comprueba con KiCad)
  1. Abre {nombre}.kicad_pcb en KiCad (PCB Editor).
  2. Inspeccionar → Comprobador de reglas de diseño (DRC) → Ejecutar. No debe haber errores.
  3. Archivo → Salidas de fabricación → Gerbers: capas F.Cu, B.Cu, F.Mask, B.Mask, F.Silkscreen,
     B.Silkscreen y Edge.Cuts → Trazar. En el mismo diálogo, «Generar archivos de taladros…» (Excellon).
  4. Comprime los Gerber y los taladros en un .zip y súbelo al fabricante (JLCPCB: 2 capas,
     {sustrato}).

Validado solo en simulación: mide la antena fabricada antes de fiarte.
Manual (ajuste con marcas, puentes y red en π): {url}/blob/main/MANUAL.md
Generado con Chirptenna (AGPL-3.0): {url}
"""


def exportar(texto):
    """Zip con la placa (.kicad_pcb), la huella (.kicad_mod), el DXF si hay ezdxf, el diseño y un LÉEME."""
    e, clave, p = _entrada(texto)
    nombre = nombre_valido(e.get('nombre') or 'antena')
    f_MHz = float(e['f_MHz'])
    a = tipos.generar(clave, p, e.get('sustrato'))
    s = e.get('serigrafia') or presentacion.SERIGRAFIA_DEFECTO
    modo_logo = s.get('logo', 'grande')
    titulo = f"{tr(tipos.CATALOGO[clave].nombre).split(' (')[0]} {a.info.get('f_estimada_MHz')} MHz"
    sustrato = e.get('sustrato') or SUSTRATO_POR_DEFECTO
    extra, salida = '', io.BytesIO()
    with tempfile.TemporaryDirectory() as tmp:
        placa = os.path.join(tmp, f'{nombre}.kicad_pcb')
        seri = exp.placa_kicad(a, placa, titulo, presentacion.lineas_serigrafia(s, clave, f_MHz, nombre),
                               None if modo_logo == 'ninguno' else modo_logo)
        archivos = [(placa, f'{nombre}.kicad_pcb')]
        huella = os.path.join(tmp, 'Antenas.pretty', f'{nombre}.kicad_mod')
        exp.huella_kicad(a, huella, nombre)
        archivos.append((huella, f'Antenas.pretty/{nombre}.kicad_mod'))
        if a.reflector:
            ref = os.path.join(tmp, f'{nombre}_reflector.kicad_pcb')
            exp.placa_reflector(a, ref, titulo)
            archivos.append((ref, f'{nombre}_reflector.kicad_pcb'))
            extra += f'  {nombre}_reflector.kicad_pcb   ' + tr('Placa del reflector (va detrás, separada).') + '\n'
        try:
            import ezdxf  # noqa: F401
            ruta = os.path.join(tmp, f'{nombre}.dxf')
            exp.dxf(a, ruta)
            archivos.append((ruta, f'{nombre}.dxf'))
            extra += f'  {nombre}.dxf               ' + tr('Dibujo para EasyEDA u otros programas.') + '\n'
            if a.reflector:
                ruta = os.path.join(tmp, f'{nombre}_reflector.dxf')
                exp.dxf_reflector(a, ruta)
                archivos.append((ruta, f'{nombre}_reflector.dxf'))
        except ImportError:
            pass
        ahora = time.strftime('%Y-%m-%d %H:%M')
        diseno = {'nombre': nombre, 'tipo': clave,
                  'parametros': {k: v for k, v in p.items() if not str(k).startswith('_')},
                  'sustrato': sustrato, 'reglas': e.get('reglas') or fabricacion.REGLAS_POR_DEFECTO,
                  'f_objetivo_MHz': f_MHz, 'ancho_banda_MHz': float(e['bw_MHz']), 'notas': e.get('notas', ''),
                  'serigrafia': dict(s), 'creado': ahora, 'modificado': ahora, 'origen': 'web',
                  'resumen': {k: a.info[k] for k in ('f_estimada_MHz', 'placa_mm', 'ganancia_estimada_dBi',
                                                    'fr4_quitado_%') if k in a.info}}
        with zipfile.ZipFile(salida, 'w', zipfile.ZIP_DEFLATED) as z:
            for ruta, arc in archivos:
                z.write(ruta, f'{nombre}/{arc}')
            z.writestr(f'{nombre}/diseno.json', json.dumps(diseno, ensure_ascii=False, indent=2, default=float))
            z.writestr(f'{nombre}/LEEME.txt', tr(LEEME, version=__version__, nombre=nombre, titulo=titulo,
                                                 extra=extra, sustrato=tr(sustrato), url=URL_PROYECTO))
    return salida.getvalue(), _json({'nombre': nombre, 'serigrafia': seri})
