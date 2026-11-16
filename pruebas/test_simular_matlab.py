"""Pruebas del motor de MATLAB sin MATLAB: la entrada que se le pasa y cómo se leen sus resultados (salida simulada)."""
import numpy as np
import pytest

from antenas import simular_matlab, tipos
from antenas.simulacion import centro_banda

F = 2441.75e6


def _antena(clave='dipolo'):
    p = tipos.dimensionar(clave, F)
    p.pop('_aviso', None)
    return tipos.generar(clave, p)


def test_entrada_lleva_cobre_contorno_y_alimentacion():
    a = _antena()
    d = simular_matlab.entrada(a, tipos.sustrato(), 2.5, 2000, 3000, 21)
    assert d['er'] == 4.5 and d['h_mm'] == 1.6 and d['puntos'] == 21
    assert d['cobre_superior'][0]['hueco'] == 0 and len(d['cobre_superior'][0]['x']) >= 4
    assert len(d['contorno']['x']) == len(d['contorno']['y']) >= 4
    x, y = d['alimentacion_mm']
    assert x == pytest.approx(0.0) and y == pytest.approx(0.75)          # borde (0,0) + 0,5 mm de cobre + 0,25 mm de línea
    assert 'theta_deg' not in d


def test_entrada_con_diagrama_usa_la_rejilla_de_openems():
    d = simular_matlab.entrada(_antena(), tipos.sustrato(), 2.5, 2000, 3000, 21, f_diagrama_MHz=2441.75)
    assert d['theta_deg'][0] == 0 and d['theta_deg'][-1] == 180 and len(d['theta_deg']) == 61
    assert d['phi_deg'][-1] == 360 and len(d['phi_deg']) == 61


def test_anillos_separa_exterior_y_huecos():
    from shapely.geometry import box
    g = box(0, 0, 10, 10).difference(box(3, 3, 6, 6))
    a = simular_matlab.anillos(g)
    assert [r['hueco'] for r in a] == [0, 1] and {r['poli'] for r in a} == {1}


def test_no_soporta_lo_que_no_modela():
    a = _antena()
    assert simular_matlab.no_soporta(a, tipos.sustrato()) is None
    a.reflector = {'contorno': a.contorno, 'separacion_mm': 5}
    assert 'reflector' in simular_matlab.no_soporta(a)
    a.reflector = None
    a.vias = [(0, 5)]
    assert 'vías' in simular_matlab.no_soporta(a)
    a.vias = []
    a.puerto = dict(a.puerto, tipo='pasante')
    assert 'coaxial' in simular_matlab.no_soporta(a)


def test_no_soporta_sustrato_de_cuatro_capas():
    class S4:
        capas = 4
    assert 'dos capas' in simular_matlab.no_soporta(_antena(), S4())


def test_simular_con_salida_de_matlab_simulada(monkeypatch):
    f = np.linspace(0.6*F, 1.4*F, 25)
    # resonancia a 1,02·F con un S11 profundo: Γ = (Z−50)/(Z+50) con Z = 50 + j·k·(f − f0)
    z = 50 + 1j*0.2*(f - 1.02*F)/1e6 + 1.0
    s = (z - 50)/(z + 50)
    salida = {'f_MHz': (f/1e6).tolist(), 's11_re': s.real.tolist(), 's11_im': s.imag.tolist(),
              'D_grid': (np.full((61, 61), 2.1)).tolist()}
    monkeypatch.setattr(simular_matlab, '_lanzar', lambda datos, progreso: salida)
    monkeypatch.setattr(simular_matlab, 'disponible', lambda: (True, ''))
    r = simular_matlab.simular(_antena(), tipos.sustrato(), F, progreso=lambda m: None)
    assert r['precision'] == 'MATLAB' and r['celdas'] == 0
    assert abs(r['f_resonancia_Hz']/F - 1.02) < 0.02
    assert r['banda_Hz'][0] is not None and r['s11_min_dB'] < -20
    assert r['directividad_dBi'] == pytest.approx(2.1) and r['directividad_dBi_grid'].shape == (61, 61)
    assert len(r['theta']) == 61 and len(r['phi']) == 61 and r['zin'].shape == r['f_Hz'].shape
    res = simular_matlab.resumen(r)
    assert res['directividad_dBi'] == 2.1 and res['banda_MHz'][0] < res['banda_MHz'][1]


def test_simular_sin_banda_cae_a_la_reactancia(monkeypatch):
    f = np.linspace(0.6*F, 1.4*F, 25)
    z = 20 + 1j*(f - F)/F*400                                  # nunca baja de −10 dB, pero la reactancia cruza el cero en F
    s = (z - 50)/(z + 50)
    salida = {'f_MHz': (f/1e6).tolist(), 's11_re': s.real.tolist(), 's11_im': s.imag.tolist(), 'D_grid': []}
    monkeypatch.setattr(simular_matlab, '_lanzar', lambda datos, progreso: salida)
    monkeypatch.setattr(simular_matlab, 'disponible', lambda: (True, ''))
    r = simular_matlab.simular(_antena(), tipos.sustrato(), F, progreso=lambda m: None)
    assert r['banda_Hz'] == (None, None) and abs(r['f_resonancia_Hz']/F - 1) < 0.03
    assert 'directividad_dBi' not in r and any('−10 dB' in a for a in r['avisos'])
    assert simular_matlab.resumen(r)['directividad_dBi'] is None


def test_simular_rechaza_antena_no_soportada(monkeypatch):
    a = _antena()
    a.vias = [(0, 5)]
    with pytest.raises(ValueError):
        simular_matlab.simular(a, tipos.sustrato(), F)


def test_sin_matlab_dice_por_que(monkeypatch):
    monkeypatch.setattr(simular_matlab, 'ejecutable', lambda: None)
    ok, motivo = simular_matlab.disponible()
    assert not ok and 'MATLAB' in motivo
