/*
 * AI Healthcare Companion & Smart Vital Tracker
 * ESP32 Hardware Integration Firmware Stub (Reference Only)
 * MAX30102 + SOS Button + GPS + HTTP Ingestion
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

// Wi-Fi Credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Backend API Configuration
const char* serverUrl = "http://192.168.1.100:8000/api/v1/readings";
const char* sosUrl = "http://192.168.1.100:8000/api/v1/sos";
const char* deviceApiKey = "demo-device-key-change-me";
const char* deviceId = "ESP32-VITAL-01";

// Pin definitions
const int SOS_BUTTON_PIN = 4;
MAX30105 particleSensor;

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 1000; // 1 reading per second

void setup() {
  Serial.begin(115200);
  pinMode(SOS_BUTTON_PIN, INPUT_PULLUP);

  Serial.println("[ESP32] Connecting to Wi-Fi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[ESP32] Connected. IP: " + WiFi.localIP().toString());

  // Initialize MAX30102
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("[WARN] MAX30102 not detected. Check wiring.");
  } else {
    particleSensor.setup();
    particleSensor.setPulseAmplitudeRed(0x0A);
    particleSensor.setPulseAmplitudeGreen(0);
  }
}

void loop() {
  // 1. Check SOS button press (Active LOW)
  if (digitalRead(SOS_BUTTON_PIN) == LOW) {
    sendEmergencySOS();
    delay(1000); // 1s debounce
  }

  // 2. Periodic vital reading transmission
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();
    sendVitalReading();
  }
}

void sendVitalReading() {
  if (WiFi.status() != WL_CONNECTED) return;

  long irValue = particleSensor.getIR();
  String signalQuality = "good";
  float bpm = 75.0;
  float spo2 = 98.0;
  float tempC = 36.6;

  // Finger detection check
  if (irValue < 50000) {
    signalQuality = "no_finger";
  }

  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Key", deviceApiKey);

  String payload = "{";
  payload += "\"device_id\":\"" + String(deviceId) + "\",";
  if (signalQuality != "no_finger") {
    payload += "\"bpm\":" + String(bpm) + ",";
    payload += "\"spo2\":" + String(spo2) + ",";
  } else {
    payload += "\"bpm\":null,";
    payload += "\"spo2\":null,";
  }
  payload += "\"temp_c\":" + String(tempC) + ",";
  payload += "\"lat\":23.1815,";
  payload += "\"lng\":79.9864,";
  payload += "\"signal_quality\":\"" + signalQuality + "\"";
  payload += "}";

  int httpCode = http.POST(payload);
  if (httpCode > 0) {
    Serial.println("[ESP32] Reading sent. Response: " + String(httpCode));
  } else {
    Serial.println("[ESP32] Error sending reading: " + http.errorToString(httpCode));
  }
  http.end();
}

void sendEmergencySOS() {
  if (WiFi.status() != WL_CONNECTED) return;

  Serial.println("[ESP32] 🚨 Triggering Hardware SOS panic alert!");
  HTTPClient http;
  http.begin(sosUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Key", deviceApiKey);

  String payload = "{\"device_id\":\"" + String(deviceId) + "\",\"lat\":23.1815,\"lng\":79.9864,\"details\":\"ESP32 Hardware Button SOS Triggered\"}";
  int httpCode = http.POST(payload);
  Serial.println("[ESP32] SOS Response code: " + String(httpCode));
  http.end();
}
