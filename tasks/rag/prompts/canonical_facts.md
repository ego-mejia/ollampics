# Hechos canónicos — Helion Robotics

Estos hechos deben aparecer **idénticos** en todos los documentos que los referencien. No los contradigas.

## Empresa
- Nombre: **Helion Robotics**
- Fundación: **2019**
- Sede: **Querétaro, México**
- CEO: **Adriana Castellanos**
- Directora de Operaciones: **Mariana Tello**

## Producto: Helion-X3
- Lanzamiento: **abril de 2024**, sucesor del Helion-X2
- Peso: **45 kg**
- Dimensiones: **1.20 m alto × 0.60 m ancho × 0.40 m fondo**
- Carga útil: **18 kg**
- Batería: **LiFePO₄ 1.5 kWh, autonomía 8 horas**
- Velocidad máxima: **2.1 m/s**
- Sensores: LiDAR Hesai XT16, IMU 9-DOF, cámara estéreo 4K, 2 sensores térmicos
- Modos de operación: **Standard**, **Eco**, **Precision**, **Emergency**
- Conectividad: Wi-Fi 6E, Ethernet Gigabit, opcional 5G mmWave
- Firmware actual: **v3.4.1** (mayo 2026)

## API pública
- Versión actual: **v3.0.0** (lanzada **15 abril 2026**)
- Endpoint base: `https://api.helionrobotics.com/v3`
- Cambio breaking v3.0.0: header `X-Helion-Auth` reemplaza a `Authorization`

## Protocolo de sobrecarga térmica
- Al detectar sobrecarga, el robot entra en **modo seguro**: reduce potencia al **20%**, notifica al operador vía webhook, registra incidente en `/var/helion/incidents/`.
- Si la temperatura sigue subiendo durante **30 segundos**: **shutdown total**.
- Umbrales: motor > 85°C o chassis > 70°C.

## RR.HH.
- Vacaciones: **21 días pagados/año**, hasta **5 días** acumulables al siguiente año.
- Licencia parental: **16 semanas pagadas** (madres y padres).
- Per diem internacional: **USD 85/día**; doméstico: **MXN 1200/día**.
- Vuelos: business class si > 8 horas; premium economy si > 4 horas.
- Días por enfermedad: **15 días/año**; justificante médico después del **3er día consecutivo**.

## Estilo
- Tono técnico, claro, sin marketing speech.
- Unidades del SI.
- Fechas: `DD mes AAAA` (ej. "15 abril 2026").
- Versiones: `vMAJOR.MINOR.PATCH`.
- Idioma: **español**.
