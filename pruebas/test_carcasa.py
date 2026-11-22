"""Carcasa 3D: mallas cerradas, volumen coherente, bloques de simulación y STL."""
import math
import os
import struct

import pytest

from antenas import carcasa, tipos

S = 'FR4 JLC 1,6 mm'


def _antena(clave='dipolo'):
    return tipos.generar(clave, tipos.dimensionar(clave, 2441.75e6, {}, S), S)


def test_mallas_con_volumen_positivo_y_razonable():
    a = _antena()
    r = carcasa.generar(a, 1.6, {})
    vb, vt = carcasa.volumen_mm3(r['base']), carcasa.volumen_mm3(r['tapa'])
    assert vb > 0 and vt > 0                      # normales hacia fuera
    d = r['dims']
    caja = (d['xo1'] - d['xo0'])*(d['yo1'] - d['yo0'])*(d['z_arriba'] - d['z_fondo'])
    hueco = (d['xi1'] - d['xi0'])*(d['yi1'] - d['yi0'])*(d['z_arriba_in'] - d['z_fondo_in'])
    assert vb + vt < caja - 0.5*hueco             # es una carcasa hueca, no un bloque


def test_la_pared_mas_gruesa_pesa_mas():
    a = _antena()
    fino = carcasa.volumen_mm3(carcasa.generar(a, 1.6, {'pared': 1.2})['base'])
    grueso = carcasa.volumen_mm3(carcasa.generar(a, 1.6, {'pared': 2.4})['base'])
    assert grueso > fino


def test_bloques_cubren_la_placa_con_holgura_y_dejan_el_hueco_del_conector():
    a = _antena()
    c = carcasa.completar({})
    con = carcasa.bloques(a, 1.6, c)
    sin = carcasa.bloques(a, 1.6, dict(c, abertura=0, fijacion='adhesivo'))
    assert len(con) > len(sin) == 6               # suelo, tapa y cuatro paredes; el hueco parte una pared
    x0, y0, x1, y1 = a.contorno.bounds
    assert min(b['caja'][0] for b in sin) <= x0 - c['holgura'] - c['pared'] + 1e-6
    assert all(b['er'] == carcasa.MATERIALES['PLA'][0] for b in sin)


def test_stl_binario(tmp_path):
    a = _antena()
    r = carcasa.exportar_stl(a, 1.6, str(tmp_path), 'prueba', {})
    for pieza in ('base', 'tapa'):
        n = os.path.getsize(r[pieza])
        triangulos = struct.unpack('<I', open(r[pieza], 'rb').read(84)[80:84])[0]
        assert n == 84 + 50*triangulos and triangulos > 100


def test_no_vale_con_varias_placas():
    a = _antena()
    a.reflector = {'contorno': a.contorno, 'separacion_mm': 10}
    assert carcasa.no_soporta(a)
    with pytest.raises(ValueError):
        carcasa.generar(a, 1.6, {})


def test_parametros_se_limitan():
    c = carcasa.completar({'pared': 99, 'material': 'oro', 'radio': -1})
    assert c['pared'] == carcasa.LIMITES['pared'][1] and c['material'] == 'PLA' and c['radio'] == carcasa.LIMITES['radio'][0]


@pytest.mark.parametrize('fijacion', ['rosca', 'tuerca', 'inserto'])
@pytest.mark.parametrize('tornillo', ['M2', 'M2.5', 'M3'])
def test_fijaciones_dan_malla_valida_y_metal(fijacion, tornillo):
    a = _antena()
    c = {'fijacion': fijacion, 'tornillo': tornillo}
    r = carcasa.generar(a, 1.6, c)
    assert carcasa.volumen_mm3(r['base']) > 0 and carcasa.volumen_mm3(r['tapa']) > 0
    b = carcasa.bloques(a, 1.6, c)
    metal = [x for x in b if x['tipo'] == 'metal']
    assert len(metal) == 4*(3 if fijacion != 'rosca' else 2)      # cabeza + caña (+ tuerca o inserto) por esquina
    assert all(x['caja'][2] < x['caja'][5] for x in metal)
    assert all(x['tipo'] == 'dielectrico' for x in carcasa.sin_metal(b))


def test_adhesivo_no_lleva_metal_ni_orejetas_y_pesa_menos():
    a = _antena()
    pegada = carcasa.generar(a, 1.6, {'fijacion': 'adhesivo'})
    rosca = carcasa.generar(a, 1.6, {'fijacion': 'rosca'})
    assert not [x for x in carcasa.bloques(a, 1.6, {'fijacion': 'adhesivo'}) if x['tipo'] == 'metal']
    assert carcasa.volumen_mm3(pegada['base']) < carcasa.volumen_mm3(rosca['base'])


def test_diseno_antiguo_con_tornillos_se_traduce_a_fijacion():
    assert carcasa.completar({'tornillos': 1})['fijacion'] == 'rosca'
    assert carcasa.completar({'tornillos': 0})['fijacion'] == 'adhesivo'


def test_lista_de_materiales_y_fibra_de_vidrio():
    for k in ('PLA', 'PETG', 'ABS', 'ASA', 'PC', 'PA12', 'PA6', 'PLA-GF', 'PETG-GF', 'ABS-GF', 'PA-GF'):
        er, tand = carcasa.MATERIALES[k]
        assert 2.0 < er < 5.0 and 0.0 < tand < 0.05 and k in carcasa.DESCRIPCIONES
        assert carcasa.completar({'material': k})['material'] == k
    # la fibra de vidrio sube la εr del plástico base, y el nailon húmedo/cargado más
    assert carcasa.MATERIALES['PETG-GF'][0] > carcasa.MATERIALES['PETG'][0]
    assert carcasa.MATERIALES['ABS-GF'][0] > carcasa.MATERIALES['ABS'][0]
    assert carcasa.MATERIALES['PA-GF'][0] > carcasa.MATERIALES['PA12'][0]
    # CF y similares no están: son conductores
    assert not any('CF' in k for k in carcasa.MATERIALES)


def test_el_relleno_baja_la_er_efectiva():
    macizo = carcasa.propiedades({'material': 'PETG'})
    medio = carcasa.propiedades({'material': 'PETG', 'relleno': 50})
    poco = carcasa.propiedades({'material': 'PETG', 'relleno': 20})
    assert macizo == carcasa.MATERIALES['PETG']
    assert 1.0 < poco[0] < medio[0] < macizo[0]
    assert poco[1] < medio[1] < macizo[1] or poco[1] < macizo[1]          # menos material, menos pérdida
    assert carcasa.propiedades({'material': 'Personalizado', 'er': 3.1, 'tand': 0.02, 'relleno': 30}) == (3.1, 0.02)   # el medido va tal cual
    assert carcasa.completar({'relleno': 5})['relleno'] == carcasa.LIMITES['relleno'][0]
    # los bloques de simulación usan la εr efectiva
    a = _antena()
    assert all(b['er'] == pytest.approx(medio[0]) for b in carcasa.bloques(a, 1.6, {'material': 'PETG', 'relleno': 50, 'fijacion': 'adhesivo'}) if b['tipo'] == 'dielectrico')


def test_la_tendencia_con_la_frecuencia_es_la_generica_documentada():
    er0, t0 = carcasa.MATERIALES['PETG']
    # a la frecuencia de referencia no cambia nada
    assert carcasa.propiedades({'material': 'PETG'}, carcasa.F_REF) == pytest.approx((er0, t0))
    assert carcasa.propiedades({'material': 'PETG'}) == (er0, t0)
    er9, t9 = carcasa.propiedades({'material': 'PETG'}, 868e6)
    assert er9 == pytest.approx(er0*(1 + 0.03*math.log10(2.4e9/868e6)))        # +1,3 % por la tendencia de 3 %/década
    assert er9 > er0 and t9 < t0 and t9 == pytest.approx(t0*(868e6/2.4e9)**0.3)  # más εr y menos pérdida hacia abajo
    # acotada a 0,3–6 GHz y sin escalar el material Personalizado (medido por el usuario)
    assert carcasa.propiedades({'material': 'PETG'}, 1e6) == carcasa.propiedades({'material': 'PETG'}, carcasa.F_MIN)
    assert carcasa.propiedades({'material': 'Personalizado', 'er': 3.1, 'tand': 0.02}, 868e6) == (3.1, 0.02)
    # los bloques de simulación usan la frecuencia que se pide
    a = _antena()
    b868 = carcasa.bloques(a, 1.6, {'material': 'PETG', 'fijacion': 'adhesivo'}, 868e6)[0]['er']
    b24 = carcasa.bloques(a, 1.6, {'material': 'PETG', 'fijacion': 'adhesivo'}, 2.4e9)[0]['er']
    assert b868 > b24 == pytest.approx(er0)
