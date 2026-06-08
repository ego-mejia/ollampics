# Helion-X3 — Manual técnico

## Resumen ejecutivo

El Helion-X3 es un robot móvil autónomo de servicio pesado, sucesor del Helion-X2, lanzado en abril de 2024. Diseñado para operaciones en interiores y exteriores controladas, integra sensores multiespectrales, modos de operación configurables y conectividad de alto ancho de banda. Su batería LiFePO₄ de 1.5 kWh proporciona hasta 8 horas de autonomía, y su firmware v3.4.1 (mayo 2026) habilita funciones de seguridad avanzadas y un API REST v3.0.0. Este manual cubre especificaciones físicas, sensores, modos de operación, conectividad, mantenimiento, actualización de firmware, códigos de error y garantía.

## Especificaciones físicas

| Característica     | Valor                          |
|--------------------|--------------------------------|
| Peso               | 45 kg                          |
| Altura             | 1.20 m                         |
| Ancho              | 0.60 m                         |
| Fondo              | 0.40 m                         |
| Carga útil máxima  | 18 kg                          |
| Batería            | LiFePO₄ 1.5 kWh (autonomía 8 h)|
| Velocidad máxima   | 2.1 m/s                        |

La estructura del chasis es de aleación de aluminio y acero inoxidable, con grado de protección IP54. La batería es extraíble y puede ser reemplazada en campo sin herramientas especializadas.

## Sensores y percepción

El Helion-X3 utiliza una suite de sensores redundante para navegación, detección de obstáculos y monitoreo térmico.

- **LiDAR Hesai XT16**: Escáner láser de 16 canales con campo de visión horizontal de 360° y vertical de 30°. Alcance máximo de 100 m con precisión ±2 cm. Utilizado para mapeo simultáneo y localización (SLAM) y detección de obstáculos estáticos y dinámicos.
- **IMU 9-DOF**: Unidad de medición inercial con acelerómetro, giróscopo y magnetómetro. Proporciona orientación (roll, pitch, yaw) a 200 Hz. Se calibra cada 500 horas de operación o tras impactos superiores a 5 G.
- **Cámara estéreo 4K**: Dos sensores RGB de 3840×2160 píxeles con lentes gran angular (110°). Utilizada para reconocimiento de objetos, lectura de códigos QR y clasificación de terreno. La profundidad se calcula mediante visión estéreo hasta 15 m.
- **Sensores térmicos**: Dos sensores infrarrojos de matriz (80×60 píxeles) montados en los laterales. Detectan puntos calientes (≥40 °C) a una distancia de hasta 5 m. Activan el modo seguro en caso de sobrecarga térmica en el entorno del robot.

## Modos de operación

El robot ofrece cuatro modos seleccionables mediante la interfaz de usuario o la API. Cada modo ajusta la velocidad, el consumo energético y la latencia de procesamiento.

### Standard
- **Uso**: Operación general en entornos con baja densidad de obstáculos.
- **Consumo relativo**: 100% (nominal).
- **Latencia típica**: 50 ms entre captura de sensor y comando de actuación.
- **Velocidad máxima**: 2.1 m/s.

### Eco
- **Uso**: Misiones de larga duración donde se prioriza la autonomía sobre la velocidad.
- **Consumo relativo**: 65% (reduce potencia de motores y frecuencia de escaneo LiDAR).
- **Latencia típica**: 80 ms.
- **Velocidad máxima**: 1.2 m/s.
- La batería se extiende aproximadamente 30% respecto al modo Standard.

### Precision
- **Uso**: Navegación en corredores estrechos, carga/descarga de precisión o inspección detallada.
- **Consumo relativo**: 120% (mayor procesamiento de cámara estéreo y fusion de sensores).
- **Latencia típica**: 30 ms.
- **Velocidad máxima**: 0.8 m/s.
- Activa el filtrado temporal del LiDAR a 20 Hz en lugar de 10 Hz.

### Emergency
- **Uso**: Activado automáticamente por el sistema de seguridad o manualmente por el operador. Detiene el robot y reduce potencia al 20%.
- **Consumo relativo**: 20% (motores limitados a torque bajo, sensores en modo seguro).
- **Latencia típica**: 10 ms (respuesta inmediata).
- **Velocidad máxima**: 0.3 m/s.
- El robot permanece en este modo hasta que se recibe un comando de desactivación explícito tras verificar condiciones seguras.

## Conectividad

- **Wi-Fi 6E**: Banda de 6 GHz, compatible con estándar IEEE 802.11ax. Velocidad máxima teórica de 9.6 Gbps. Requiere un punto de acceso con soporte WPA3.
- **Ethernet Gigabit**: Puerto RJ45 10/100/1000 BASE-T para conexión cableada. Utilizado durante la configuración inicial o en entornos con interferencias RF.
- **Opción 5G mmWave**: Módulo complementario para operación remota en exteriores sin infraestructura Wi-Fi. Bandas n257, n258, n260. Latencia típica <10 ms.

**Requisitos de red recomendados**:
- Ancho de banda mínimo para teleoperación: 20 Mbps subida/bajada.
- Para operación autónoma con streaming de video: 50 Mbps.
- El robot soporta desconexión y reconexión automática; en caso de pérdida de conectividad por más de 15 segundos, activa el modo Emergency y detiene el movimiento.

## Mantenimiento programado

Las siguientes tareas deben realizarse conforme a las horas de operación acumuladas. Se recomienda registrar cada intervención en el sistema de gestión local.

| Intervalo (horas) | Tarea                                           |
|-------------------|-------------------------------------------------|
| 100               | Limpieza externa del chasis y sensores          |
| 200               | Verificación de firmware y actualización si aplica |
| 250               | Reemplazo de filtros de ventilación LiDAR       |
| 500               | Calibración de IMU y ajuste de parámetros       |
| 1000              | Lubricación de rodamientos de ruedas y juntas   |
| 1500              | Revisión de conexiones eléctricas y apriete de tornillería |
| 2000              | Sustitución de batería LiFePO₄ (vida útil estimada) |

- **Filtros LiDAR**: Cada 250 horas se deben limpiar o reemplazar los filtros de polvo del cabezal láser. El polvo acumulado reduce el alcance y la precisión.
- **Calibración IMU**: Cada 500 horas el sistema solicita una calibración automática girando el robot 360° en cada eje. Si se omite, el rendimiento de localización puede degradarse.
- **Lubricación**: Usar grasa de litio grado 2 en los rodamientos de las ruedas motrices y en la junta de elevación (si aplica). No superar 2 g por punto.

## Actualización de firmware

El firmware actual es **v3.4.1**, lanzado en mayo de 2026. Todas las actualizaciones se realizan a través de la herramienta de línea de comandos `helionctl`.

**Procedimiento**:
1. Descargar el paquete de firmware desde el portal de Helion Robotics (formato `.hfirm`).
2. Verificar la integridad del archivo mediante SHA256. El checksum oficial se publica en la página de descarga.
3. Conectar el robot a una fuente de alimentación estable y a la red local Ethernet o Wi-Fi.
4. Ejecutar: `helionctl upgrade /ruta/al/archivo.hfirm`
5. El robot valida el paquete, aplica la actualización y reinicia automáticamente. El proceso dura aproximadamente 5 minutos.
6. Confirmar la versión instalada con `helionctl status`.

**Rollback**: Si la actualización falla o el robot no arranca correctamente, se puede revertir a la versión anterior:
- `helionctl rollback --target <versión>` (por ejemplo `--target v3.3.0`).
- El robot debe estar en modo seguro (Emergency) para permitir el rollback.
- No se admite rollback cruzado de versiones mayores (p.ej. de v3 a v2).

**Notas**:
- Durante la actualización no se debe interrumpir la alimentación ni la conexión de red.
- En caso de fallo de energía, el robot se recupera automáticamente al restablecerse la corriente y continúa la actualización desde el punto de control.

## Códigos de error comunes

| Código    | Descripción                                    | Acción correctiva |
|-----------|------------------------------------------------|-------------------|
| ERR_001   | Sobrecarga térmica en motor (>85°C)            | Detener operación, dejar enfriar. Revisar ventilación y carga mecánica. |
| ERR_002   | Sobrecarga térmica en chassis (>70°C)          | Reducir carga útil y velocidad. Si persiste, shutdown total tras 30 s. |
| ERR_003   | Fallo de comunicación LiDAR                   | Verificar conexión física y reiniciar robot. Reemplazar cable si es necesario. |
| ERR_004   | Error de calibración IMU                       | Ejecutar calibración automática en superficie plana. Si falla, contactar soporte. |
| ERR_005   | Batería críticamente baja (<5%)                | Dirigir robot a estación de carga. Si no hay estación, activar modo Eco. |
| ERR_006   | Fallo en cámara estéreo                        | Limpiar lentes. Si persiste, reemplazar cámara. |
| ERR_007   | Error de red: timeout en API                   | Verificar conectividad y reiniciar módulo Wi-Fi/5G. |
| ERR_008   | Fallo de firmware: checksum incorrecto         | Reinstalar firmware desde USB o red. Ejecutar `helionctl recovery`. |

Para errores críticos (ERR_001, ERR_002, ERR_008), el robot ingresa automáticamente en modo Emergency y registra el incidente en `/var/helion/incidents/`.

## Garantía

Helion Robotics ofrece una garantía limitada de **24 meses** a partir de la fecha de entrega para el modelo Helion-X3.

**Cobertura**:
- Defectos de fabricación en materiales y mano de obra.
- Batería LiFePO₄: 12 meses o 2000 ciclos de carga, lo que ocurra primero.
- Componentes electrónicos (sensores, placas): 24 meses.

**Exclusiones**:
- Daños por mal uso, modificaciones no autorizadas, exposición a productos químicos o agua (más allá de IP54).
- Desgaste normal de piezas móviles (ruedas, rodamientos, juntas) que requieren mantenimiento programado.
- Fallos por no realizar las tareas de mantenimiento indicadas en este manual.

**Proceso de escalamiento**:
1. Registrar el incidente en el portal de soporte (soporte.helionrobotics.com) con número de serie y código de error.
2. El equipo técnico responderá en un máximo de 8 horas hábiles (lunes a viernes, GMT-6).
3. Si se requiere reemplazo de piezas, estas se envían a la dirección registrada con costo cubierto por Helion Robotics.
4. Para garantía internacional, contactar a la oficina de Querétaro o al distribuidor local autorizado.

---

*Documento generado con base en la información canónica de Helion Robotics. Versión del manual: 1.0 (julio 2026).*