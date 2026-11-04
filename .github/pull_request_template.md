## Qué cambia y por qué · What and why

<!-- Describe el cambio y el motivo. Enlaza el issue si lo hay: «Cierra #…» -->

## Cómo lo has probado · How it was tested

<!-- Marca lo que aplique y deja los resultados. Ver CONTRIBUTING.md -->

- [ ] La interfaz arranca y el cambio funciona en ella (`iniciar.bat`)
- [ ] `python herramientas/comprobar_tipos.py` sale todo «OK» (genera y exporta todos los tipos a 868 MHz y 2,4 GHz con el **DRC de KiCad**)
- [ ] Simulado (si cambia la geometría que se simula): resonancia, banda −10 dB, ganancia y η antes / después
- [ ] Medido en una placa real (¡mejor aún!)
- [ ] No aplica (documentación, textos…)

## Comprobaciones · Checklist

- [ ] Código, comentarios y textos de la interfaz en castellano
- [ ] Sin Gerber, taladros, `.zip` de fabricación ni otros archivos generados
- [ ] Sin rutas ni datos personales
- [ ] `antenas/problemas.py` y la tabla de los README actualizados si cambia el estado de un tipo
- [ ] Si toca `vna/`: nunca se envía `save` y se restaura el estado del equipo
- [ ] Acepto que esta aportación se publique con las licencias del proyecto (AGPL-3.0 / CC BY-NC 4.0)
