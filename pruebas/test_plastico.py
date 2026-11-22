"""Cupón C: εeff de la microstrip con una muestra encima, inversión de εr y tanδ y extracción del pico de S21."""
import numpy as np
import pytest

from antenas import carcasa, materiales, plastico

H, ER = 1.6, 4.5
W = round(materiales.ancho_microstrip(50, ER, H), 2)


def test_solver_coincide_con_hammerstad_sin_muestra():
    e, fr = plastico.eps_eff(W, H, ER)
    assert e == pytest.approx(materiales.eps_eff_microstrip(ER, H, W), rel=0.02)
    assert 0.85 < fr['sustrato'] < 0.95 and fr['muestra'] == 0.0


def test_una_muestra_sube_la_eps_eff_y_lleva_energia():
    e0 = plastico.eps_eff(W, H, ER)[0]
    e1, fr = plastico.eps_eff(W, H, ER, 2.8, 3.0)
    assert e1 > e0 and fr['muestra'] > 0.1
    e2, _ = plastico.eps_eff(W, H, ER, 2.8, 3.0, gap=0.3)         # con rendija de aire el efecto baja
    assert e0 < e2 < e1
    assert plastico.eps_eff(W, H, ER, 6.0, 3.0)[0] > e1           # más εr, más εeff


@pytest.mark.parametrize('er_real,t', [(2.8, 3.0), (6.0, 2.0)])
def test_la_inversion_recupera_la_er(er_real, t):
    e0 = plastico.eps_eff(W, H, ER)[0]
    e1 = plastico.eps_eff(W, H, ER, er_real, t)[0]
    f0 = 2400.0
    f1 = f0*np.sqrt(e0/e1)                                         # la frecuencia que daría el anillo
    r = plastico.medir(f0, f1, t, w_mm=W, h_mm=H, er_sustrato=ER)
    assert r['ok'] and r['er'] == pytest.approx(er_real, abs=0.02)
    assert r['er_incertidumbre'] > 0


def test_tand_se_recupera_con_los_q():
    t, er_m, tand_m, tand_sub = 3.0, 2.8, 0.02, 0.02
    e0, fr0 = plastico.eps_eff(W, H, ER)
    e1, fr1 = plastico.eps_eff(W, H, ER, er_m, t)
    q_otras = 400.0                                                # conductor y radiación
    q0 = 1/(1/q_otras + fr0['sustrato']*tand_sub)
    q1 = 1/(1/q_otras + fr1['sustrato']*tand_sub + fr1['muestra']*tand_m)
    r = plastico.medir(2400.0, 2400.0*np.sqrt(e0/e1), t, w_mm=W, h_mm=H, er_sustrato=ER, q_vacio=q0, q_cargado=q1, tand_sustrato=tand_sub)
    assert r['tand'] == pytest.approx(tand_m, rel=0.02)
    assert r['tand_fiable']


def test_cociente_imposible_no_revienta():
    r = plastico.medir(2400.0, 2500.0, 3.0, w_mm=W, h_mm=H, er_sustrato=ER)     # una muestra no sube la frecuencia
    assert not r['ok'] and r['motivo']


def test_pico_de_s21_y_q():
    f = np.linspace(2.0e9, 2.4e9, 801)
    f0, q = 2.2e9, 120.0
    s21 = 10*np.log10(1e-8 + 1e-3/(1 + (2*q*(f - f0)/f0)**2))        # lorentziana de potencia: −3 dB a ±f0/(2Q)
    r = plastico.parametros_pico(f, s21)
    assert r['f_MHz'] == pytest.approx(2200.0, abs=0.6)
    assert r['q_cargado'] == pytest.approx(q, rel=0.03)
    assert r['q_propio'] > r['q_cargado']
    assert plastico.parametros_pico(f, np.full_like(f, -60.0)) is None           # sin pico


def test_material_personalizado_de_la_carcasa():
    c = {'material': 'Personalizado', 'er': 3.4, 'tand': 0.02}
    assert carcasa.propiedades(c) == (3.4, 0.02)
    assert carcasa.propiedades({'material': 'PLA'}) == carcasa.MATERIALES['PLA']
    assert carcasa.completar({'material': 'Personalizado', 'er': 99})['er'] == carcasa.LIMITES['er'][1]


def test_stl_de_las_muestras_con_taladros(tmp_path):
    import os
    import struct
    r = plastico.muestras_stl(str(tmp_path), grosores=(2.0, 3.0))
    nombres = {os.path.basename(p) for p in r['archivos']}
    assert nombres == {f'muestra_{s}_{t}mm.stl' for s in plastico.STUBS for t in ('2', '3')}      # una tira por stub y grosor, sin pisador
    for ruta in r['archivos']:
        n = struct.unpack('<I', open(ruta, 'rb').read(84)[80:84])[0]
        assert os.path.getsize(ruta) == 84 + 50*n and n > 100
    # el volumen es el de la tira menos cuatro taladros de M3
    from shapely.geometry import Point, box
    m = plastico.muestra_de('S43')
    pos = [(x - m['origen'][0], y - m['origen'][1]) for x, y in plastico.agujeros('S43')]
    prismas = [(0.0, 3.0, box(0, 0, m['ancho'], m['largo']), '+')] + [(-0.01, 3.01, Point(x, y).buffer(plastico.D_PASO_M3/2, quad_segs=16), '-') for x, y in pos]
    v = carcasa.volumen_mm3(carcasa.malla(prismas))
    esperado = 3.0*(m['ancho']*m['largo'] - 4*np.pi*(plastico.D_PASO_M3/2)**2)
    assert v == pytest.approx(esperado, rel=0.01)


def test_las_tiras_caben_en_la_placa_y_los_taladros_lejos_del_stub():
    for k, s in plastico.STUBS.items():
        m = plastico.muestra_de(k)
        x0, y0 = m['origen']
        assert x0 >= 0 and x0 + m['ancho'] <= 100 and y0 >= 0 and y0 + m['largo'] <= 100           # dentro de la placa de 100 × 100 mm
        for x, y in plastico.agujeros(k):
            assert x0 < x < x0 + m['ancho'] and y0 < y < y0 + m['largo']
            assert abs(x - s['x']) - 3.01/2 > 5.0                                                     # ≥ 5 mm del borde de la pista: la tuerca de nailon no pesa

def test_el_pisador_sobre_el_anillo_falsearia_la_er():
    # una cubierta de 4 mm del mismo plástico sobre la muestra sube la εr aparente (por eso no hay pisador)
    e0 = plastico.eps_eff(3.01, 1.6, 4.5)[0]
    sin = plastico.eps_eff(3.01, 1.6, 4.5, 2.8, 3.0)
    con = plastico.eps_eff(3.01, 1.6, 4.5, 2.8, 3.0, 0.0, (2.8, 4.0, 0.0))
    assert con[0] > sin[0] * 1.01 and con[1]['cubierta'] > 0.01
    assert e0 < sin[0]

def test_leer_s21_de_un_s2p_y_de_un_csv():
    s2p = '! prueba\n# HZ S RI R 50\n' + '\n'.join(f'{2.0e9 + k*1e6:.0f} 0.1 0 {0.01*(1 + k)} 0 {0.01*(1 + k)} 0 0.1 0' for k in range(3)) + '\n'
    f, s = plastico.leer_s21(s2p)
    assert len(f) == 3 and f[0] == 2.0e9 and s[0] == pytest.approx(-40.0, abs=0.01) and s[1] == pytest.approx(20*np.log10(0.02), abs=0.01)
    f, s = plastico.leer_s21('frecuencia_MHz,S21_dB\n2000,-50\n2001,-45\n')
    assert f[0] == pytest.approx(2.0e9) and s[1] == -45.0
    f, s = plastico.leer_s21('2400000000;-33.5\n2400100000;-30\n')
    assert f[1] == pytest.approx(2.4001e9)


def test_er_del_fr4_desde_el_anillo():
    r = plastico.er_fr4(plastico.REF_ANILLOS['R2G4']['f_MHz'])
    assert r['ok'] and r['er'] == pytest.approx(4.5, abs=0.01)
    assert plastico.er_fr4(2300.0)['er'] > 4.5 > plastico.er_fr4(2450.0)['er']       # más εr, frecuencia más baja
    assert not plastico.er_fr4(1000.0)['ok']
    assert not plastico.er_fr4(2400.0, anillo='no_existe')['ok']


def test_la_correccion_3d_recupera_la_er_de_las_simulaciones_de_openems():
    # resonancias del anillo R2G4 simuladas en openEMS 3D (cupon/simulaciones/): vacío 2397,1 MHz
    for er_real, t, f1 in ((2.8, 3.0, 2219.2), (6.0, 2.0, 2042.9), (4.0, 3.0, 2130.3)):
        con = plastico.medir(2397.1, f1, t, w_mm=3.01, anillo='R2G4', con_incertidumbre=False)
        sin = plastico.medir(2397.1, f1, t, w_mm=3.01, con_incertidumbre=False)
        assert con['er'] == pytest.approx(er_real, rel=0.02) and con['calibrado_3d'] and not con['fuera_de_calibracion']
        assert sin['er'] > con['er'] and not sin['calibrado_3d']              # sin corregir, la εr sale alta
    assert plastico.medir(2397.1, 2100.0, 0.8, w_mm=3.01, anillo='R2G4', con_incertidumbre=False)['fuera_de_calibracion']      # grosor fuera de lo calibrado


def test_resonancias_de_un_stub_en_s11():
    # línea abierta ideal: Z = −j·Z0·cot(βL); resuena (X: − → +) en L = λg/4 y 3λg/4
    f = np.linspace(100e6, 2800e6, 4001)
    L, eps = 0.043, 3.5
    beta_l = 2*np.pi*f*np.sqrt(eps)/299792458.0*L
    z = -1j*50/np.tan(beta_l) + 1.0                     # + 1 Ω de pérdida serie
    s11 = (z - 50)/(z + 50)
    r = plastico.resonancias_stub(f, s11)
    esperadas = [299792458.0/(4*L*np.sqrt(eps))/1e6*k for k in (1, 3)]
    assert len(r) >= 2
    for e, got in zip(esperadas, r):
        assert got['f_MHz'] == pytest.approx(e, rel=0.002) and got['R_ohm'] == pytest.approx(1.0, abs=0.05) and got['dXdf_ohm_MHz'] > 0
    assert plastico.elegir_resonancia(r, esperadas[1])['f_MHz'] == r[1]['f_MHz']
    assert plastico.elegir_resonancia(r, 5000.0) is None


# resonancias de los stubs en la simulación 3D (cupon/simulaciones/stub_*.json, εr 4,5; muestra de 24 mm, tanδ 0): (εr real, grosor, modo, f_vacío, f_cargada)
CASOS_3D_STUB = [(2.8, 3.0, 1, 869.678, 812.9), (6.0, 2.0, 1, 869.678, 756.1), (4.0, 4.0, 2, 2624.945, 2359.2), (10.0, 3.0, 1, 869.678, 688.8),
                 (2.2, 2.0, 2, 2624.945, 2519.8), (6.0, 4.0, 2, 2624.945, 2235.3)]


@pytest.mark.parametrize('er_real,t,modo,f0,f1', CASOS_3D_STUB)
def test_el_stub_recupera_la_er_de_la_simulacion_3d(er_real, t, modo, f0, f1):
    r = plastico.medir_stub(f0, f1, t, modo=modo, con_incertidumbre=False)
    assert r['ok'] and r['er'] == pytest.approx(er_real, rel=0.04) and r['calibrado_3d'] and not r['fuera_de_calibracion']


def test_incertidumbre_del_stub_incluye_el_conector():
    r = plastico.medir_stub(869.678, 812.9, 3.0, modo=1)
    sin = plastico.medir_stub(869.678, 812.9, 3.0, modo=1, con_incertidumbre=False)
    assert r['er'] == sin['er'] and 0.02 < r['er_incertidumbre'] < 0.3


def test_er_del_fr4_con_varios_stubs():
    # las resonancias 3D de εr 4,5: sale 4,65 (la malla de FDTD da un εeff +3 % sobre el cuasiestático); el lanzamiento sale de unos 3 mm
    r = plastico.er_fr4_stubs({'S43': 869.678, 'S59': 646.167, 'S86': 450.3}, 1)
    assert r['ok'] and 4.4 < r['er'] < 4.85 and 2.0 < r['lanzamiento_mm'] < 4.5
    assert plastico.er_fr4_stubs({'S43': 869.678}, 1)['ok'] is False              # con un solo stub no se puede quitar el conector
    # un FR4 de más εr baja todas las frecuencias y sube la εr medida
    r2 = plastico.er_fr4_stubs({'S43': 869.678*0.97, 'S59': 646.167*0.97, 'S86': 450.3*0.97}, 1)
    assert r2['er'] > r['er']


def test_tand_del_stub_sube_con_la_resistencia():
    base = dict(f_vacio_MHz=869.678, f_cargado_MHz=812.9, grosor_mm=3.0, modo=1, r_vacio=1.3, alfa_c_1ghz=0.0, con_incertidumbre=False)
    bajo = plastico.medir_stub(r_cargado=1.35, **base)
    alto = plastico.medir_stub(r_cargado=1.8, **base)
    assert alto['tand'] > bajo['tand']
    assert 'tand_fiable' in alto and 'tand_incertidumbre' in alto
