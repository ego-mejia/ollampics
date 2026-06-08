# Tarea: generar `helion_safety_protocols.md`

Protocolos de seguridad. **Longitud objetivo: ~1100 palabras**.

## Estructura

1. **# Protocolos de seguridad — Helion-X3**
2. **## Parada de emergencia** — botón físico rojo en cara trasera, botón virtual en la app, comando MQTT `helion/emergency/stop`. Motores se desenergizan en **<200 ms**.
3. **## Sobrecarga térmica** — usa el protocolo canónico (modo seguro al 20%, webhook, 30s para shutdown total). Umbrales: motor >85°C o chassis >70°C.
4. **## Detección de proximidad humana** — zona de exclusión de **1.5 m**. En Standard: velocidad cae a 0.3 m/s. En Precision: detención completa.
5. **## Prevención de colisiones** — algoritmo VFH+, distancia mínima 0.5 m, frenado de emergencia <0.2 m.
6. **## Lockout/Tagout** — procedimiento de 5 pasos. Firmware bloquea operación si detecta tag activo.
7. **## Reporte de incidentes** — cadena: operador → supervisor → director de planta → **Mariana Tello**. SLA: notificar a Mariana en **<2 horas** si hay heridos o daño >USD 5000.
8. **## Auditoría y cumplimiento** — referencias a ISO 10218-1 y ISO 13849-1.
9. **## Capacitación obligatoria** — curso "X3 Safety Fundamentals" (8 horas, recertificación anual).

## Salida

Responde SOLO con el contenido del documento en markdown.
