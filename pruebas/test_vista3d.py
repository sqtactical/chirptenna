"""Vista 3D: se dibuja cualquier tipo, la modular también explosionada y con el diagrama de un resultado."""
import numpy as np
import pytest

from antenas import tipos, vista3d

F = 2441.75e6


def _antena(clave, extra=None):
    p = tipos.dimensionar(clave, F, extra)
    p.pop('_aviso', None)
    return tipos.generar(clave, p)


def _tipos_de_malla(fig):
    return [t.type for t in fig.data]


@pytest.mark.parametrize('clave', sorted(tipos.CATALOGO))
def test_todos_los_tipos_se_dibujan(clave):
    fig = vista3d.figura(_antena(clave), 1.6)
    tipos_ = _tipos_de_malla(fig)
    assert tipos_.count('mesh3d') >= 2 and 'scatter3d' in tipos_       # FR4 y al menos un cobre, más el contorno y el conector
    for t in fig.data:
        if t.type == 'mesh3d':
            assert len(t.x) == len(t.y) == len(t.z) and max(max(t.i), max(t.j), max(t.k)) < len(t.x)


def test_el_grosor_se_exagera_en_placas_largas_y_se_avisa():
    larga = _antena('colineal_dipolos', {'modular': 1, 'elementos': 4})
    f = vista3d.figura(larga, 1.6)
    assert 'exagerado' in f.layout.title.text
    zs = np.concatenate([np.array(t.z, float) for t in f.data if t.type == 'mesh3d'])
    assert zs.max() > 1.6                                              # la placa dibujada es más gruesa que los 1,6 mm
    pequena = _antena('dipolo')
    assert 'exagerado' not in vista3d.figura(pequena, 1.6).layout.title.text or vista3d._dim(pequena) < 130


def test_modular_armada_marca_las_uniones_y_explosionada_dibuja_cada_placa():
    a = _antena('colineal_dipolos', {'modular': 1, 'elementos': 4})
    armada = vista3d.figura(a, 1.6)
    assert any(t.type == 'scatter3d' and t.name and 'Uniones' in t.name for t in armada.data)
    expl = vista3d.figura(a, 1.6, explosionada=True)
    losas = [t for t in expl.data if t.type == 'mesh3d' and t.name == 'FR4']
    assert len(losas) == sum(m['cantidad'] for m in a.modulos) == 4              # inicio, 2 módulos y final
    rotulos = [t.text[0] for t in expl.data if t.type == 'scatter3d' and t.mode == 'text']
    assert len(rotulos) == 4 and any('1/2' in r for r in rotulos) and any('2/2' in r for r in rotulos)
    # explosionada: las placas no se solapan en Y
    rangos = sorted((min(t.y), max(t.y)) for t in losas)
    assert all(b[0] > a_[1] for a_, b in zip(rangos, rangos[1:]))


def test_no_modular_ignora_explosionada():
    a = _antena('dipolo')
    assert len(vista3d.figura(a, 1.6, explosionada=True).data) == len(vista3d.figura(a, 1.6).data)


def test_panel_dibuja_el_reflector_y_sus_hilos():
    a = _antena('panel_dipolos')
    fig = vista3d.figura(a, 1.6)
    reflector = [t for t in fig.data if t.type == 'mesh3d' and t.name == 'Reflector']
    assert len(reflector) == 1 and np.allclose(reflector[0].z, -a.reflector['separacion_mm'])


def test_el_diagrama_se_centra_en_la_placa_y_marca_el_maximo():
    a = _antena('monopolo_recto')
    theta, phi = np.arange(0, 181, 3.0), np.arange(0, 361, 6.0)
    d = np.zeros((len(theta), len(phi)))
    d[10, 20] = 5.0                                                    # un único máximo en θ 30°, φ 120°
    fig = vista3d.figura(a, 1.6, diagrama=(theta, phi, d))
    sup = [t for t in fig.data if t.type == 'surface']
    assert len(sup) == 1 and np.array(sup[0].z).shape == d.shape
    assert 'θ 30°' in fig.layout.title.text and 'φ 120°' in fig.layout.title.text
    x0, y0, x1, y1 = a.contorno.bounds
    assert np.nanmean(np.array(sup[0].x)) == pytest.approx((x0 + x1)/2, abs=0.2*max(x1 - x0, 1))
