"""Pruebas rápidas del núcleo (sin openEMS): `python -m pytest pruebas` desde la raíz del proyecto."""
import math
import os
import sys

import pytest
from shapely.geometry import box

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from antenas import ajuste, bucle, geometria, materiales, tipos  # noqa: E402

BANDAS = (868e6, 2441.75e6)


def test_sexp():
    from antenas import sexp
    r = sexp.leer('(a (b 1 2.5 "x y") (c)\n (b foo))')
    assert r[0] == 'a' and r[1] == ['b', 1.0, 2.5, 'x y'] and r[2] == ['c']
    assert len(sexp.hijos(r, 'b')) == 2 and sexp.hijo(r, 'c') == ['c']
    with pytest.raises(ValueError):
        sexp.leer('(a (b)')


def test_importar_kicad_placa_propia(tmp_path):
    # F3.6: una placa exportada por el programa se importa con el mismo contorno y casi el mismo cobre
    from antenas import exportar, importar_kicad
    p = tipos.dimensionar('ifa', 2441.75e6, {'integrada': 1, 'placa_x': 30, 'placa_y': 50})
    a = tipos.generar('ifa', p)
    ruta = str(tmp_path / 'p.kicad_pcb')
    exportar.placa_kicad(a, ruta)
    pl = importar_kicad.placa(ruta)
    assert pl['ancho_mm'] == pytest.approx(30, abs=0.01) and pl['alto_mm'] == pytest.approx(50, abs=0.01)
    assert pl['contorno'].area == pytest.approx(a.contorno.area, rel=0.01)
    masa = pl['cobre']['B.Cu']
    assert masa.area == pytest.approx(a.cobre('B.Cu').area, rel=0.02)
    assert pl['grosor_mm'] == pytest.approx(1.6)
    # y se puede usar como placa anfitriona: el contorno y la masa coinciden con los de la antena integrada normal
    dato = importar_kicad.a_dato(pl, 'prueba')
    q = dict(p, placa_importada=dato)
    b = tipos.generar('ifa', q)
    assert b.contorno.area == pytest.approx(a.contorno.area, rel=0.01)
    assert b.info['placa_importada'] == 'prueba'
    assert b.cobre('B.Cu').area == pytest.approx(a.cobre('B.Cu').area, rel=0.05)
    # girar 90° intercambia ancho y alto
    g = importar_kicad.girar_dato(dato, 90)
    assert (g['ancho'], g['alto']) == pytest.approx((50, 30), abs=0.01) and g['giro'] == 90


def test_importar_kicad_placa_en_l():
    # placa no rectangular escrita a mano: un chaflán con arco, una pista en F.Cu, una zona en B.Cu y un pad girado
    from antenas import importar_kicad
    pcb = '''(kicad_pcb (version 20240108) (generator "x") (general (thickness 1.6))
     (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (44 "Edge.Cuts" user))
     (gr_line (start 100 100) (end 150 100) (layer "Edge.Cuts"))
     (gr_line (start 150 100) (end 150 160) (layer "Edge.Cuts"))
     (gr_line (start 150 160) (end 120 160) (layer "Edge.Cuts"))
     (gr_arc (start 120 160) (mid 110 150) (end 100 140) (layer "Edge.Cuts"))
     (gr_line (start 100 140) (end 100 100) (layer "Edge.Cuts"))
     (segment (start 105 150) (end 140 150) (width 0.3) (layer "F.Cu") (net 1))
     (zone (net 1) (net_name "GND") (layer "B.Cu") (polygon (pts (xy 101 101) (xy 149 101) (xy 149 159) (xy 101 159)))
      (filled_polygon (layer "B.Cu") (pts (xy 101 101) (xy 149 101) (xy 149 159) (xy 101 159))))
     (footprint "X" (layer "F.Cu") (at 110 110 90) (pad "1" smd rect (at 2 0) (size 2 1) (layers "F.Cu")))
    )'''
    pl = importar_kicad.leer_texto(pcb)
    assert (pl['ancho_mm'], pl['alto_mm']) == pytest.approx((50, 60), abs=0.01)
    assert 2700 < pl['contorno'].area < 2900          # 50 × 60 menos el chaflán redondeado
    assert pl['cobre']['B.Cu'].area == pytest.approx(48*58 - 0, abs=1)   # zona entera en la placa recortada por el chaflán o no
    # huella girada 90° (antihorario en pantalla): su +x local apunta hacia arriba, así que el pad queda en (110, 108) en KiCad,
    # x = 10, y = 60 - 8 = 52 en el modelo, y de 1 × 2 mm (la huella lo gira)
    pad = pl['cobre']['F.Cu']
    from shapely.geometry import Point
    assert pad.contains(Point(10, 52.9)) and not pad.contains(Point(11.2, 52))
    d = importar_kicad.a_dato(pl, 'L')
    p = tipos.dimensionar('ifa', 2441.75e6, {'integrada': 1, 'placa_importada': d})
    a = tipos.generar('ifa', p)
    assert a.contorno.area == pytest.approx(pl['contorno'].area, rel=0.001)
    assert any('cobre de tu placa' in v for v in a.info.get('avisos', []))


def test_sustrato_4_capas(tmp_path):
    # F3.5: la línea de 50 Ω sale de ~0,4 mm (h_ref 0,21 mm), solo vale integrada y la placa lleva In1.Cu e In2.Cu con la masa
    from antenas import exportar
    S = 'FR4 JLC 4 capas 1,6 mm'
    s = materiales.SUSTRATOS[S]
    assert s.capas == 4 and s.h_linea == pytest.approx(0.2104) and s.z_masa == pytest.approx(s.h - 0.2104)
    assert materiales.SUSTRATOS['FR4 JLC 1,6 mm'].z_masa == 0 and materiales.SUSTRATOS['FR4 JLC 1,6 mm'].h_linea == 1.6
    p = tipos.dimensionar('ifa', 2441.75e6, {'integrada': 1, 'placa_x': 30, 'placa_y': 50}, S)
    a = tipos.generar('ifa', p, S)
    assert 0.3 < a.info['ancho_linea_50ohm_mm'] < 0.5 and a.info['capas_cobre'] == 4
    with pytest.raises(ValueError):
        tipos.generar('parche_rectangular', {}, S)
    ruta = str(tmp_path / 'p.kicad_pcb')
    exportar.placa_kicad(a, ruta)
    t = open(ruta, encoding='utf-8').read()
    assert '(1 "In1.Cu" signal)' in t and '(layer "In1.Cu")' in t and '(layer "In2.Cu")' in t and 'stackup' in t
    assert 'In1.Cu' not in (lambda b: exportar.placa_kicad(b, str(tmp_path / 'q.kicad_pcb')) or open(str(tmp_path / 'q.kicad_pcb'), encoding='utf-8').read())(
        tipos.generar('ifa', tipos.dimensionar('ifa', 2441.75e6, {'integrada': 1, 'placa_x': 30, 'placa_y': 50})))


def test_importar_kicad_arco():
    from antenas import importar_kicad
    pts = importar_kicad._arco((10, 0), (0, 10), (-10, 0))       # semicírculo por arriba (en KiCad y es hacia abajo, da igual)
    assert all(abs(math.hypot(x, y) - 10) < 1e-6 for x, y in pts)
    assert pts[0] == pytest.approx((10, 0)) and pts[-1] == pytest.approx((-10, 0))
    assert len(pts) >= 12 and max(abs(x) for x, _ in pts) <= 10 + 1e-9   # flecha ≤ 0,1 mm: 12 tramos en el semicírculo


def test_consejos_integracion():
    # F3.10: la antena integrada trae las reglas de integración; la de prueba, no
    from antenas import consejos
    p = tipos.dimensionar('ifa', 2441.75e6, {'integrada': 1, 'placa_x': 30, 'placa_y': 50})
    cs = consejos.consejos(tipos.generar('ifa', p), 2441.75e6)
    reglas = [t for c, t in cs if c == 'integración']
    assert len(reglas) >= 5
    assert any('6 mm' in t for t in reglas)  # cosido cada λ/20 = 6 mm a 2,4 GHz
    p0 = tipos.dimensionar('ifa', 2441.75e6, {})
    assert not [1 for c, _ in consejos.consejos(tipos.generar('ifa', p0), 2441.75e6) if c == 'integración']


@pytest.mark.parametrize('n', [0, 1, 2, 3])
def test_longitud_koch(n):
    # cada iteración multiplica la longitud por 4/3
    assert geometria.longitud(geometria.koch(n)) == pytest.approx((4/3)**n, rel=1e-6)


@pytest.mark.parametrize('n', [0, 1, 2])
def test_area_sierpinski(n):
    # cada iteración deja 3/4 del área
    a0 = geometria.sierpinski(0, 10, 10).area
    assert geometria.sierpinski(n, 10, 10).area == pytest.approx(a0*0.75**n, rel=1e-3)


def test_ancho_microstrip_50_ohm():
    assert 2.9 <= materiales.ancho_microstrip(50, 4.5, 1.6) <= 3.1


@pytest.mark.parametrize('zl', [10 + 5j, 20 - 30j, 3 + 40j, 120 + 60j, 200 - 80j])
def test_redes_l_adaptan(zl):
    f = 868e6
    sols = ajuste.redes_l(zl, f)
    assert sols
    # los valores E24 redondean (y con R de pocos ohmios, mucho): la mejor solución debe quedar por debajo de -10 dB
    assert sols[0]['s11_dB'] < -10


@pytest.mark.parametrize('clave', sorted(tipos.CATALOGO))
@pytest.mark.parametrize('f_obj', BANDAS)
def test_dimensionar_estimar(clave, f_obj):
    p = tipos.dimensionar(clave, f_obj)
    if '_aviso' in p:
        pytest.skip('fuera de los límites del tipo a esta banda')
    p = {k: v for k, v in p.items() if not k.startswith('_')}
    f = tipos.estimar_f(clave, p)
    assert abs(f - f_obj)/f_obj <= 0.01


@pytest.mark.parametrize('clave', ['ifa', 'monopolo_recto', 'monopolo_meandro', 'monopolo_koch'])
@pytest.mark.parametrize('posicion', [0, 1, 2])
def test_antena_integrada(clave, posicion):
    # F3.1: placa de 30 × 50 mm a 2,4 GHz; ni masa ni cobre de ninguna capa en la zona de antena, salvo la propia antena
    p = tipos.dimensionar(clave, 2441.75e6, {'integrada': 1, 'placa_x': 30, 'placa_y': 50, 'posicion': posicion})
    a = tipos.generar(clave, p)
    x0, y0, x1, y1 = a.contorno.bounds
    assert (x1 - x0, y1 - y0) == pytest.approx((30, 50), abs=1e-6)
    assert a.info['integrada'] is True
    assert a.cobre('B.Cu').intersection(a.zona_libre).area == pytest.approx(0, abs=1e-6)
    assert a.contorno.contains(a.cobre('F.Cu')) and a.contorno.contains(a.cobre('B.Cu'))
    # el radiador cae en la zona (salvo el arranque de la pista y el cortocircuito de la IFA, que entran en la masa)
    zx0, zy0, zx1, zy1 = a.zona_libre.bounds
    assert a.radiador.intersection(box(zx0 - 1, zy0, zx1 + 1, zy1 + 1)).within(a.zona_libre.buffer(1e-6))


def test_huella_integrar(tmp_path):
    # F3.3: la huella lleva la zona de exclusión (todas las capas de cobre), el pad pasante de la vía de la IFA y el lado de Edge.Cuts
    from antenas import exportar
    p = tipos.dimensionar('ifa', 2441.75e6, {'integrada': 1, 'placa_x': 30, 'placa_y': 50})
    a = tipos.generar('ifa', p)
    ruta = tmp_path / 'h.kicad_mod'
    exportar.huella_kicad(a, str(ruta), 'h_integrar', integrar=True)
    t = ruta.read_text(encoding='utf-8')
    assert '(keepout (tracks not_allowed) (vias not_allowed)' in t and '(copperpour not_allowed)' in t
    assert '(layers "F.Cu" "B.Cu")' in t
    assert '(pad "2" thru_hole' in t and 'Dwgs.User' in t
    exportar.huella_kicad(a, str(ruta), 'h')              # la huella normal no lleva zona
    assert '(keepout' not in ruta.read_text(encoding='utf-8')
    ej = tmp_path / 'e.kicad_pcb'
    exportar.placa_ejemplo_integrada(a, str(ej), 'h_integrar')
    assert ej.read_text(encoding='utf-8').count('(keepout') == 2      # la de la huella y la de la placa


def test_entorno_bloques():
    # F3.7: los predefinidos caen donde se dice (carcasa a 1 mm sobre y bajo la placa, batería detrás, mano a 5 mm por debajo)
    from antenas import entorno
    a = tipos.generar('monopolo_recto', tipos.dimensionar('monopolo_recto', 2441.75e6, {}))
    h = 1.6
    b = entorno.bloques(a, h, ['carcasa', 'bateria', 'mano'])
    assert [x['nombre'] for x in b] == ['carcasa', 'carcasa', 'bateria', 'mano']
    arriba, abajo, bat, mano = b
    assert arriba['caja'][2] == pytest.approx(h + 1.0) and arriba['caja'][5] == pytest.approx(h + 2.5)
    assert abajo['caja'][5] == pytest.approx(-1.0) and bat['tipo'] == 'metal' and bat['caja'][5] == pytest.approx(-1.0)
    assert mano['caja'][5] == pytest.approx(-5.0) and mano['er'] == 30
    n = entorno.neutro(mano)
    assert n['er'] == 1.0 and n['tand'] == 0 and n['sigma'] == 0 and n['caja'] == mano['caja']
    with pytest.raises(KeyError):
        entorno.bloques(a, h, ['no_existe'])


def test_integrada_no_cabe():
    # la IFA de 868 MHz no cabe en 40 mm de ancho: error claro con lo que falta
    p = tipos.dimensionar('ifa', 868e6, {'integrada': 1, 'placa_x': 40, 'placa_y': 80})
    with pytest.raises(ValueError, match='faltan'):
        tipos.generar('ifa', p)


def test_bucle_estimar_f():
    p = tipos.CATALOGO['bucle'].defectos()
    f = bucle.estimar_f(p)
    assert 1e8 < f < 6e9
    # la fórmula sola y la calibrada difieren poco (el factor es ~1,03-1,05)
    assert abs(bucle.estimar_f(p, calibrada=False)/f - 1) < 0.15
    # más condensador -> frecuencia más baja
    assert bucle.estimar_f(dict(p, capacidad_pF=p['capacidad_pF']*2)) < f
