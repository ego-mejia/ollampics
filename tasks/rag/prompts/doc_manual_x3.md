# Tarea: generar `helion_manual_x3.md`

Genera un manual técnico del Helion-X3 en markdown. **Longitud objetivo: ~1800 palabras**.

## Estructura obligatoria

Usa `#` para el título y `##` para secciones. Las secciones, en orden:

1. **# Helion-X3 — Manual técnico**
2. **## Resumen ejecutivo** — 1 párrafo.
3. **## Especificaciones físicas** — incluye tabla markdown con peso, dimensiones, carga útil, batería.
4. **## Sensores y percepción** — describe cada sensor (LiDAR Hesai XT16, IMU 9-DOF, cámara estéreo 4K, 2 sensores térmicos).
5. **## Modos de operación** — sub-sección por modo (Standard, Eco, Precision, Emergency). Para cada uno: cuándo usarlo, consumo energético relativo, latencia típica.
6. **## Conectividad** — Wi-Fi 6E, Ethernet, opcional 5G, requisitos de red.
7. **## Mantenimiento programado** — intervalos en horas de operación; inventa números coherentes (filtros LiDAR cada N horas, calibración IMU cada N, lubricación cada N).
8. **## Actualización de firmware** — pasos (CLI `helionctl upgrade`, checksum SHA256, rollback). Menciona que v3.4.1 fue el upgrade de mayo 2026.
9. **## Códigos de error comunes** — tabla con al menos 8 códigos (`ERR_001` a `ERR_008`) con descripción y acción correctiva.
10. **## Garantía** — duración, qué cubre, cómo escalar.

## Salida

Responde con SOLO el contenido del documento en markdown. Sin meta-comentarios, sin código fences alrededor del markdown.
