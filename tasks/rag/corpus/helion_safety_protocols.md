# Protocolos de seguridad — Helion-X3

Este documento describe los protocolos de seguridad obligatorios para la operación del robot Helion-X3 (firmware v3.4.1, lanzado en abril 2024). Todos los operadores, supervisores y personal de mantenimiento deben conocer y aplicar estos procedimientos antes de cualquier interacción con el equipo.

## Parada de emergencia

El Helion-X3 dispone de tres mecanismos independientes para detener el robot en una situación de peligro:

- **Botón físico**: pulsador rojo de tipo seta, ubicado en la cara trasera del chasis, a 0.80 m del suelo. Al presionarlo, los motores se desenergizan en menos de 200 ms.
- **Botón virtual**: disponible en la interfaz de la aplicación Helion Control (Android/iOS, versión 3.0.0 o superior). La acción es equivalente al botón físico.
- **Comando MQTT**: cualquier cliente autorizado puede publicar el mensaje `helion/emergency/stop` en el broker designado. El robot reacciona en el mismo tiempo de 200 ms.

Una vez activada la parada de emergencia, el firmware mantiene los motores desenergizados hasta que se realice un reset manual. No es posible reanudar la operación desde la app ni por MQTT.

## Sobrecarga térmica

El sistema de gestión térmica monitorea continuamente la temperatura del motor y del chasis. Los umbrales críticos son:

- Motor: superior a 85 °C.
- Chasis: superior a 70 °C.

Al superar cualquiera de estos umbrales, el robot entra en **modo seguro**:

1. Reduce la potencia a un 20 % del máximo.
2. Notifica al operador mediante un webhook configurado en la API (endpoint `POST /webhooks/thermal`).
3. Registra el incidente en el archivo `/var/helion/incidents/` con marca de tiempo y valores de temperatura.

Si la temperatura permanece por encima del umbral durante 30 segundos consecutivos, el firmware ejecuta un **shutdown total** sin posibilidad de reanudación remota. Solo personal autorizado puede reencender el equipo tras verificar que la fuente de sobrecalentamiento ha sido corregida.

## Detección de proximidad humana

El Helion-X3 establece una zona de exclusión de 1.5 m alrededor de su perímetro. Esta zona es monitoreada por los sensores LiDAR (Hesai XT16) y la cámara estéreo 4K.

- En modo **Standard**: si se detecta una persona dentro de la zona, la velocidad se reduce automáticamente a 0.3 m/s hasta que la persona se aleje.
- En modo **Precision**: la detección provoca una detención completa del robot. Solo puede reanudar su trayectoria después de que el operador confirme visualmente que la zona está despejada y presione el botón de reanudación en la app.

Esta funcionalidad no sustituye la presencia de un operador responsable. El robot no debe operar en áreas donde se prevea la presencia de personas no capacitadas.

## Prevención de colisiones

El firmware implementa el algoritmo VFH+ (Vector Field Histogram) para la navegación reactiva. Los parámetros de seguridad son:

- Distancia mínima permitida a obstáculos: 0.5 m.
- Frenado de emergencia activado cuando la distancia es inferior a 0.2 m.

El frenado de emergencia detiene el robot en menos de 100 ms y desenergiza los motores. Tras el frenado, el robot permanece inmovilizado hasta que el operador realice una evaluación de la situación y rearme el sistema desde la app.

## Lockout/Tagout

El procedimiento de bloqueo y etiquetado (LOTO) se aplica durante tareas de mantenimiento, reparación o limpieza que requieran acceso a partes móviles o al interior del chasis. Consta de cinco pasos obligatorios:

1. **Notificar**: informar a todo el personal en el área sobre la parada.
2. **Apagar**: desconectar el robot mediante el interruptor principal o retirar la batería.
3. **Bloquear**: colocar un candado de seguridad en el interruptor o en el conector de la batería. Cada técnico utiliza su propio candado.
4. **Etiquetar**: fijar una tarjeta de advertencia con nombre, fecha y motivo del bloqueo.
5. **Verificar**: confirmar que el robot no responde a ningún comando (intentar encender desde la app o por MQTT).

El firmware v3.4.1 bloquea automáticamente cualquier comando de operación mientras detecte un tag activo en el sistema (a través del conector de servicio). Solo se puede retirar el tag y reanudar la operación tras completar el paso inverso con autorización del supervisor.

## Reporte de incidentes

La cadena de notificación para incidentes de seguridad es la siguiente:

1. Operador → Supervisor inmediato.
2. Supervisor → Director de planta.
3. Director de planta → **Mariana Tello** (Directora de Operaciones, Helion Robotics).

El SLA para notificar a Mariana Tello es de **menos de 2 horas** desde el momento en que se tiene conocimiento del incidente, cuando concurra alguna de estas condiciones:

- Lesiones personales (heridos).
- Daño material estimado superior a USD 5000.

El reporte debe incluir:

- Fecha y hora del incidente.
- Descripción detallada de lo ocurrido.
- Número de serie del robot.
- Versión de firmware.
- Condiciones ambientales (temperatura, humedad, tipo de superficie).
- Acciones inmediatas tomadas.

El registro se almacena en `/var/helion/incidents/` y se replica en la nube de Helion Robotics para auditoría.

## Auditoría y cumplimiento

El Helion-X3 cumple con las normas internacionales de seguridad para robots industriales:

- **ISO 10218-1**: requisitos de seguridad para robots en entornos industriales. El diseño del robot incluye paradas de emergencia, reducción de velocidad en presencia humana y limitación de potencia.
- **ISO 13849-1**: seguridad funcional de sistemas de control. Las funciones de seguridad (parada de emergencia, frenado de colisión, detección térmica) están categorizadas como PL d (Performance Level d) según la evaluación de riesgos realizada por el fabricante.

Se realizan auditorías internas cada seis meses y una auditoría externa anual. La documentación de cumplimiento se mantiene en el repositorio de calidad de Helion Robotics y está disponible para revisión por parte de clientes y entes reguladores.

## Capacitación obligatoria

Todo el personal que opere, mantenga o supervise el Helion-X3 debe completar el curso **"X3 Safety Fundamentals"**. Este curso tiene una duración de 8 horas e incluye:

- Conocimiento de todos los protocolos descritos en este documento.
- Simulaciones de parada de emergencia, sobrecarga térmica y lockout/tagout.
- Prueba práctica de manejo en modo Standard y Precision.

La certificación tiene una validez de un año. La recertificación anual es obligatoria, con una duración de 4 horas (repaso y actualización). Helion Robotics mantiene un registro de todas las certificaciones activas. El firmware v3.4.1 permite restringir la operación a operadores certificados mediante la vinculación de sus credenciales en la app.