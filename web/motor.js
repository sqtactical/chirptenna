// Motor de Chirptenna web: Python (Pyodide) en un Web Worker para que la página no se congele.
// Recibe {id, fn, arg} y responde {id, ok, resultado | error}. fn: catalogo, dimensionar, generar, exportar.
// Chirptenna · Copyright (C) 2026 sqtactical · AGPL-3.0

// Pyodide 0.29.3: Python 3.13, numpy 2.2, shapely 2.0.7 con GEOS 3.12 (más antiguo que el de escritorio:
// las operaciones de geometría delicadas usan grid_size para no fallar)
const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.29.3/full/';
importScripts(PYODIDE + 'pyodide.js');

let api = null;

function progreso(texto, fraccion) {
  postMessage({ progreso: texto, fraccion });
}

async function arrancar() {
  progreso('Cargando Python (Pyodide)…', 0.05);
  const py = await loadPyodide({ indexURL: PYODIDE });
  progreso('Cargando numpy y shapely…', 0.35);
  await py.loadPackage(['numpy', 'shapely', 'micropip']);
  progreso('Cargando el generador de Chirptenna…', 0.7);
  const zip = await (await fetch('py/antenas.zip', { cache: 'no-cache' })).arrayBuffer();
  py.unpackArchive(zip, 'zip', { extractDir: '/home/pyodide' });
  // ezdxf (DXF) es opcional: si no se puede instalar, el zip sale sin DXF
  try {
    progreso('Cargando ezdxf (DXF)…', 0.8);
    await py.runPythonAsync("import micropip\nawait micropip.install('ezdxf')");
  } catch (e) {
    console.warn('Sin ezdxf: se exporta sin DXF', e);
  }
  progreso('Preparando…', 0.95);
  api = py.pyimport('antenas.web_api');
  return py;
}

const listo = arrancar().then(
  () => postMessage({ listo: true }),
  (e) => { postMessage({ fallo: String(e) }); throw e; });

onmessage = async (ev) => {
  const { id, fn, arg } = ev.data;
  try {
    await listo;
    if (fn === 'exportar') {
      const r = api.exportar(arg);
      const bytes = r.get(0).toJs();
      const info = r.get(1);
      r.destroy();
      postMessage({ id, ok: true, resultado: { zip: bytes, info: JSON.parse(info) } }, [bytes.buffer]);
    } else {
      const r = fn === 'catalogo' ? api.catalogo() : api[fn](arg);
      postMessage({ id, ok: true, resultado: JSON.parse(r) });
    }
  } catch (e) {
    postMessage({ id, ok: false, error: String(e.message || e) });
  }
};
