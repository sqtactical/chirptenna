# Seguridad · Security

*English below.*

## Versiones con soporte

Chirptenna está en fase alpha: solo se corrigen fallos en la **última versión publicada** en
[Releases](https://github.com/sqtactical/chirptenna/releases).

## Cómo avisar de un fallo de seguridad

**No abras una issue pública.** Usa el aviso privado de GitHub:
pestaña **Security → Report a vulnerability**
([enlace directo](https://github.com/sqtactical/chirptenna/security/advisories/new)).

Cuenta qué versión usas, cómo reproducirlo y qué impacto tiene. Es un proyecto personal sin plazos
garantizados, pero intentaré responder en unos días y publicar el arreglo con el aviso correspondiente.

## Qué conviene saber

- La interfaz (`gui/app.py`) es un servidor web **sin autenticación** que escucha solo en `127.0.0.1`.
  Si la abres a la red con `CHIRPTENNA_HOST=0.0.0.0`, cualquiera de esa red puede usarla y escribir en
  tu carpeta de diseños. Hazlo solo en una red de confianza.
- El instalador descarga Python de python.org (comprueba la firma) y openEMS de GitHub (comprueba el
  SHA-256). Si una de esas comprobaciones falla, se detiene: no lo fuerces.
- Los archivos de diseño (`diseno.json`) y las medidas (`.s1p`) de otras personas son datos: el
  programa no ejecuta código de ellos.

---

## Supported versions

Chirptenna is in alpha: fixes go only into the **latest published version** in
[Releases](https://github.com/sqtactical/chirptenna/releases).

## Reporting a vulnerability

**Do not open a public issue.** Use GitHub's private reporting:
**Security → Report a vulnerability**
([direct link](https://github.com/sqtactical/chirptenna/security/advisories/new)).

Include the version, steps to reproduce and the impact. This is a personal project with no guaranteed
timelines, but I will try to answer within a few days and publish the fix with an advisory.

## Good to know

- The GUI (`gui/app.py`) is a web server **without authentication** that listens only on `127.0.0.1`.
  If you expose it with `CHIRPTENNA_HOST=0.0.0.0`, anyone on that network can use it and write to your
  designs folder. Only do so on a trusted network.
- The installer downloads Python from python.org (signature checked) and openEMS from GitHub (SHA-256
  checked). If a check fails it stops: do not force it.
- Other people's design files (`diseno.json`) and measurements (`.s1p`) are data: the program does
  not execute code from them.
