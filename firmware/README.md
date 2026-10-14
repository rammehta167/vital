# ESP32 Firmware Reference & Hardware Integration Guide

> **Note:** This hardware phase is a forward-looking reference for post-prototype deployment. The prototype runs complete end-to-end software simulation via `simulator/simulator.py`.

---

## Hardware Specifications (Future Phase)
1. **Microcontroller:** ESP32 Development Board (ESP-WROOM-32) with Wi-Fi & BLE.
2. **Pulse Oximeter & Heart Rate Sensor:** MAX30102 (I2C interface, address `0x57`).
3. **Temperature Sensor:** DS18B20 (OneWire) or integrated MAX30205 clinical thermometer.
4. **GPS Module:** NEO-6M / NEO-8M UART GPS module.
5. **Emergency SOS Trigger:** Tactile push button with 10kΩ pull-up resistor to GPIO 4.
6. **Accelerometer (Fall Detection):** MPU6050 6-axis Gyro/Accelerometer on I2C.

---

## Circuit Pinout Connection Matrix

| ESP32 Pin | Component Pin | Function / Protocol |
|-----------|---------------|---------------------|
| 3V3       | VCC           | 3.3V Power Supply   |
| GND       | GND           | Ground              |
| GPIO 21   | SDA           | I2C Data (MAX30102) |
| GPIO 22   | SCL           | I2C Clock (MAX30102)|
| GPIO 4    | Button Pin 1  | Emergency SOS Button|
| GPIO 16   | TXD (GPS RX)  | Serial2 RX (GPS)    |
| GPIO 17   | RXD (GPS TX)  | Serial2 TX (GPS)    |

---

## Wire-Protocol Compatibility

The firmware transmits data to the exact same FastAPI backend endpoint using HTTP POST:

- **Endpoint:** `http://<SERVER_IP>:8000/api/v1/readings`
- **Header:** `X-Device-Key: demo-device-key-change-me`
- **Content-Type:** `application/json`

### Payload Schema:
```json
{
  "device_id": "ESP32-VITAL-01",
  "bpm": 74.5,
  "spo2": 98.2,
  "temp_c": 36.8,
  "lat": 23.1815,
  "lng": 79.9864,
  "signal_quality": "good",
  "ts": "2026-10-13T07:30:00Z"
}
```

When the hardware SOS button is pressed:
- **Endpoint:** `http://<SERVER_IP>:8000/api/v1/sos`
- **Payload:**
```json
{
  "device_id": "ESP32-VITAL-01",
  "lat": 23.1815,
  "lng": 79.9864,
  "details": "Hardware SOS Panic Button Pressed"
}
```
