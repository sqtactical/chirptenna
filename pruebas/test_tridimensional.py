"""Antenas de varias placas no coplanares y hélices (tridimensional.py, pose.py, vista3d con pose)."""
import numpy as np
import pytest

from antenas import tipos, pose, vista3d

F = 2441.75e6
TIPOS_3D = ('diedro', 'reflector_esquina', 'helice_normal', 'helice_cuadrifilar')


def _generar(clave):
    f = 1575.42e6 if clave == 'helice_cuadrifilar' else F
    p = tipos.dimensionar(clave, f)
    p.pop('_aviso', None)
    return p, tipos.generar(clave, p)


def test_pose_gira_con_la_mano_derecha():
    # un giro de +90° alrededor de X lleva +Y a +Z, y alrededor de Y lleva +Z a +X (la misma convención que CSXCAD)
    assert np.allclose(pose.aplicar([[0, 1, 0]], {'giros': [(0, 90)]}), [[0, 0, 1]], atol=1e-9)
    assert np.allclose(pose.aplicar([[0, 0, 1]], {'giros': [(1, 90)], 'origen': (1, 2, 3)}), [[2, 2, 3]], atol=1e-9)


@pytest.mark.parametrize('clave', TIPOS_3D)
def test_genera_y_estima_la_frecuencia(clave):
    p, a = _generar(clave)
    f = 1575.42e6 if clave == 'helice_cuadrifilar' else F
    assert abs(tipos.estimar_f(clave, p) - f)/f < 0.02
    assert a.modulos, 'cada tipo lleva al menos una placa a fabricar'
    assert not a.contorno.is_empty


def test_diedro_cobre_simulado_continuo_y_fabricado_separado():
    p, a = _generar('diedro')
    assert len(a.placas3d) == 2 and [m['nombre'] for m in a.modulos] == ['centro', 'ala_derecha', 'ala_izquierda']
    # lo que se simula toca el canto de la bisagra; lo que se fabrica queda a 0,5 mm
    xh = a.info['bisagra_mm']
    assert a.cobre_sim['F.Cu'].union(a.cobre_sim['B.Cu']).bounds[2] >= xh - 1e-6
    centro = a.modulos[0]['antena']
    assert centro.cobre('F.Cu').union(centro.cobre('B.Cu')).bounds[2] <= xh - 0.5 + 1e-6
    # las alas suben a cada lado
    c = pose.caja_conjunto(a, 1.6)
    assert c[1][2] > 3.0 and c[0][0] < -xh and c[1][0] > xh


def test_diedro_a_cero_grados_es_el_dipolo_plano():
    p, a = _generar('diedro')
    plano = tipos.generar('diedro', dict(p, angulo_v=0.0))
    c = pose.caja_conjunto(plano, 1.6)
    assert c[1][2] < 1.7                                         # todo en el plano de la placa


def test_reflector_de_esquina_es_simetrico():
    p, a = _generar('reflector_esquina')
    ca, cb = (pose.caja(pl, 1.6) for pl in a.placas3d)
    assert abs(ca[0][2] + cb[1][2] - 1.6) < 0.1                  # simétricas respecto al plano de la placa del dipolo (z = h/2)
    assert ca[0][2] > 1.6                                         # el vértice truncado deja pasar la placa del dipolo
    assert [m['cantidad'] for m in a.modulos] == [1, 2]


def test_helice_normal_hilo_y_tira():
    p, a = _generar('helice_normal')
    pts = a.hilos3d[0]['puntos']
    assert abs(pts[0][2] - 1.6) < 1e-9 and abs(pts[-1][2] - 1.6 - p['altura']) < 1e-6
    largo = float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
    assert abs(largo - a.info['largo_hilo_mm'])/largo < 0.02
    tira = a.modulos[0]['antena']
    assert abs(tira.contorno.bounds[2] - np.pi*p['diametro']) < 1e-6


def test_helice_cuadrifilar_cuatro_brazos_y_sin_simulacion():
    p, a = _generar('helice_cuadrifilar')
    assert len(a.hilos3d) == 4
    assert a.info.get('sin_simulacion')


@pytest.mark.parametrize('clave', TIPOS_3D)
def test_vista3d_dibuja_las_placas_y_los_hilos(clave):
    p, a = _generar(clave)
    fig = vista3d.figura(a, 1.6)
    assert len(fig.data) > 4
    assert len(vista3d.figura(a, 1.6, explosionada=True).data) >= 3
