"""Contrato con Chirptenna VNA (la web del NanoVNA): el .s1p simulado se lee igual que uno medido."""
import os

import numpy as np

from antenas import ajuste, biblioteca


def test_s1p_simulado_ida_y_vuelta(tmp_path):
    f = np.linspace(2.0e9, 2.8e9, 21)
    s11 = 0.4 * np.exp(-1j * np.linspace(0.1, 2.0, 21))
    ruta = tmp_path / 's11_simulado.s1p'
    biblioteca.escribir_s1p(str(ruta), f, s11, 'Chirptenna · prueba')
    texto = ruta.read_text(encoding='utf-8')
    assert texto.splitlines()[0].startswith('! ')
    assert '# HZ S RI R 50' in texto            # lo que espera touchstone.js de la web VNA
    f2, s2 = ajuste.leer_s1p(texto)
    assert np.allclose(f2, f) and np.allclose(s2, s11, atol=1e-5)


def test_guardar_simulacion_copia_el_s1p(tmp_path, monkeypatch):
    monkeypatch.setenv('CHIRPTENNA_DISENOS', str(tmp_path / 'disenos'))
    origen = tmp_path / 'sim'
    origen.mkdir()
    for n in ('resultado.json', 'datos.npz', 's11_simulado.s1p'):
        (origen / n).write_text('x', encoding='utf-8')
    destino = biblioteca.guardar_simulacion('prueba_vna', str(origen))
    assert os.path.exists(os.path.join(destino, 's11_simulado.s1p'))
