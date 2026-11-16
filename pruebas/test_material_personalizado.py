"""Sustrato personalizado: su nombre lleva los valores y `tipos.sustrato` lo reconstruye (desktop, web y simulación comparten ese nombre)."""
import pytest

from antenas import materiales, tipos
from antenas.materiales import nombre_personalizado, sustrato_por_nombre

F = 2441.75e6
PTFE = 'Personalizado (εr 2,65; tanδ 0,0019; 1,65 mm)'


def test_nombre_canonico_y_ida_y_vuelta():
    assert nombre_personalizado(2.65, 0.0019, 1.65) == PTFE
    assert materiales.valores_personalizado(PTFE) == (2.65, 0.0019, 1.65)
    s = sustrato_por_nombre(PTFE)
    assert (s.er, s.tand, s.h, s.capas) == (2.65, 0.0019, 1.65, 2) and s.nombre == PTFE and 'personalizado' in s.nota


@pytest.mark.parametrize('er,tand,h,texto', [(4.5, 0.02, 1.6, '4,5; tanδ 0,02; 1,6'), (3, 0, 0.5, '3; tanδ 0; 0,5'),
                                             (10.2, 0.0023, 0.254, '10,2; tanδ 0,0023; 0,254'), (2.2, 0.00001, 0.787, '2,2; tanδ 0,00001; 0,787')])
def test_formato_sin_exponentes_ni_ceros_sobrantes(er, tand, h, texto):
    n = nombre_personalizado(er, tand, h)
    assert texto in n and 'e-' not in n
    assert materiales.valores_personalizado(n) == pytest.approx((er, tand, h))


@pytest.mark.parametrize('er,tand,h', [(0.5, 0.01, 1.6), (25, 0.01, 1.6), (4.4, -0.1, 1.6), (4.4, 0.5, 1.6), (4.4, 0.02, 0.0), (4.4, 0.02, 9.0),
                                       (None, 0.02, 1.6)])
def test_fuera_de_rango_se_rechaza(er, tand, h):
    with pytest.raises(ValueError):
        nombre_personalizado(er, tand, h)


def test_nombre_que_no_existe_sigue_siendo_keyerror():
    with pytest.raises(KeyError):
        tipos.sustrato('Unobtainium 1 mm')
    with pytest.raises(KeyError):
        tipos.sustrato('Personalizado (εr 2,65)')
    with pytest.raises(ValueError):                       # tiene el formato pero εr = 30
        tipos.sustrato('Personalizado (εr 30; tanδ 0,01; 1,6 mm)')


def test_los_de_la_tabla_no_cambian():
    assert tipos.sustrato() is materiales.SUSTRATOS[materiales.SUSTRATO_POR_DEFECTO]
    assert tipos.sustrato('RO4350B 0,76 mm').er == 3.66
    assert not materiales.es_personalizado('FR4 JLC 1,6 mm') and materiales.es_personalizado(PTFE)


def _ancho_linea(sustrato):
    p = tipos.dimensionar('monopolo_recto', F, None, sustrato)
    p.pop('_aviso', None)
    return tipos.generar('monopolo_recto', p, sustrato).puerto['ancho_linea']


def test_la_linea_de_50_ohm_usa_el_sustrato_personalizado():
    w_fr4 = _ancho_linea('FR4 JLC 1,6 mm')
    assert _ancho_linea(PTFE) > w_fr4                     # menos εr: pista más ancha para los mismos 50 Ω
    # un personalizado igual que el FR4 de JLC da la misma pista
    assert _ancho_linea(nombre_personalizado(4.5, 0.02, 1.6)) == pytest.approx(w_fr4)


def test_el_personalizado_igual_a_una_entrada_de_la_tabla_da_la_misma_antena():
    a = tipos.generar('dipolo', tipos.dimensionar('dipolo', F), 'FR4 JLC 1,6 mm')
    b = tipos.generar('dipolo', tipos.dimensionar('dipolo', F), nombre_personalizado(4.5, 0.02, 1.6))
    assert a.cobre('F.Cu').symmetric_difference(b.cobre('F.Cu')).area < 1e-6
    assert b.info['sustrato'] == nombre_personalizado(4.5, 0.02, 1.6)


@pytest.mark.parametrize('nombre,er,tol', [('PTFE ZYF255DA 1,65 mm', 2.55, 0.04), ('PTFE ZYF265D 0,9 mm', 2.65, 0.04),
                                           ('PTFE ZYF300CA-C 0,65 mm', 2.94, 0.05), ('PTFE ZYF300CA-P 1,65 mm', 3.0, 0.05)])
def test_ptfe_de_jlc_llevan_la_tolerancia_del_datasheet(nombre, er, tol):
    s = materiales.SUSTRATOS[nombre]
    assert s.er == er and s.er_tol == pytest.approx(tol/er, abs=1e-4) and s.er_tol < 0.02
    assert materiales.SUSTRATOS['FR4 JLC 1,6 mm'].er_tol == 0.05 and sustrato_por_nombre(PTFE).er_tol == 0.05


def test_analisis_de_tolerancias_usa_la_tolerancia_del_material(monkeypatch):
    from antenas import simulacion
    vistas = []

    def falsa(antena, sustrato, f_obj, *a, **k):
        vistas.append(sustrato.er)
        return {'f_resonancia_Hz': f_obj, 'banda_Hz': (f_obj*0.97, f_obj*1.03), 'paso_malla_mm': 1.0}
    monkeypatch.setattr(simulacion, 'simular', falsa)
    ant = tipos.generar('dipolo', tipos.dimensionar('dipolo', F))
    base = {'f_resonancia_Hz': F, 'banda_Hz': (F*0.97, F*1.03), 'paso_malla_mm': 1.0}
    ptfe = materiales.SUSTRATOS['PTFE ZYF265D 1,65 mm']
    r = simulacion.tolerancias(ant, ptfe, F, (F*0.99, F*1.01), base, progreso=lambda m: None)
    assert r['filas'][0]['etiqueta'] == 'εr ±1,5 %'
    assert vistas[0] == pytest.approx(2.65*(1 - 0.0151), abs=1e-3) and vistas[1] == pytest.approx(2.65*(1 + 0.0151), abs=1e-3)
    vistas.clear()
    r = simulacion.tolerancias(ant, materiales.SUSTRATOS['FR4 JLC 1,6 mm'], F, (F*0.99, F*1.01), base, progreso=lambda m: None)
    assert r['filas'][0]['etiqueta'] == 'εr ±5 %' and vistas[0] == pytest.approx(4.5*0.95)


def test_la_cache_de_simulacion_distingue_los_valores():
    from antenas.simulacion import _clave_cache
    a = tipos.generar('dipolo', tipos.dimensionar('dipolo', F))
    k1 = _clave_cache(a, sustrato_por_nombre(PTFE), 1e9, 3e9, 'normal')
    k2 = _clave_cache(a, sustrato_por_nombre(nombre_personalizado(2.65, 0.0019, 1.6)), 1e9, 3e9, 'normal')
    k3 = _clave_cache(a, sustrato_por_nombre(nombre_personalizado(2.65, 0.0030, 1.65)), 1e9, 3e9, 'normal')
    assert len({k1, k2, k3}) == 3
