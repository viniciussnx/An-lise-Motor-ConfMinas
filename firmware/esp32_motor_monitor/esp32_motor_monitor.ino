// ════════════════════════════════════════════════════════════
//  ConfiMinas — Firmware ESP32  v2.2.0
//  Motor Monitor + LEDs de Status
//
//  LEDs:
//    Amarelo (GPIO25) — circuito energizado (sempre acesa)
//    Vermelho (GPIO27) — motor parado
//    Verde    (GPIO14) — motor em funcionamento
//
//  Fluxo:
//    1. Lê sensores a cada SEND_INTERVAL_MS
//    2. POST /api/readings  → envia dados ao backend
//    3. GET  /api/esp32/health → lê is_running → controla motor + LEDs
// ════════════════════════════════════════════════════════════

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESPmDNS.h>
#include "config.h"

#if USE_DHT22
  #include <DHT.h>
  DHT dht(PIN_TEMP_DHT, DHT22);
#endif

#if USE_ADXL345
  #include <Wire.h>
  #include <Adafruit_ADXL345_U.h>
  Adafruit_ADXL345_Unified accel(12345);
#endif

// ── Estado global ────────────────────────────────────────────
static bool   motorRunning  = false;
static bool   wifiOk        = false;
static int    httpFailCount = 0;
static String resolvedHost  = "";

// ── Protótipos ───────────────────────────────────────────────
void  setupPins();
void  setupWifi();
void  resolveHost();
float readTemperature();
float readVibration();
float readCurrent();
float readVoltage();
void  setMotor(bool on);
void  updateLEDs();
void  postReading();
void  pollMotorState();

// ════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n[BOOT] ConfiMinas ESP32 v" FIRMWARE_VER);

  setupPins();

  // Amarela acende imediatamente — circuito energizado
  digitalWrite(PIN_LED_YELLOW, HIGH);

  // Estado inicial: motor parado → vermelha acesa
  setMotor(false);

#if USE_DHT22
  dht.begin();
  Serial.println("[SENSOR] DHT22 iniciado");
#else
  Serial.println("[SENSOR] LM35 (ADC) configurado");
#endif

#if USE_ADXL345
  Wire.begin();
  if (!accel.begin()) {
    Serial.println("[WARN] ADXL345 nao encontrado — usando SW-420");
  } else {
    accel.setRange(ADXL345_RANGE_16_G);
    Serial.println("[SENSOR] ADXL345 iniciado");
  }
#else
  Serial.println("[SENSOR] SW-420 (digital) configurado");
#endif

  setupWifi();
  resolveHost();

  Serial.println("[READY] Envio a cada " + String(SEND_INTERVAL_MS) + " ms");
}

// ════════════════════════════════════════════════════════════
void loop() {
  static unsigned long lastAction = 0;
  unsigned long now = millis();

  // Reconexão WiFi se cair
  if (WiFi.status() != WL_CONNECTED) {
    wifiOk = false;
    Serial.println("[WiFi] Conexao perdida — reconectando...");
    setupWifi();
    resolveHost();
    return;
  }

  if (now - lastAction >= SEND_INTERVAL_MS) {
    lastAction = now;

    // 1. Envia leituras dos sensores
    postReading();

    // 2. Verifica estado do motor no backend e atualiza GPIO + LEDs
    pollMotorState();
  }
}

// ════════════════════════════════════════════════════════════
//  SETUP — pinos e periféricos
// ════════════════════════════════════════════════════════════
void setupPins() {
  pinMode(LED_BUILTIN,     OUTPUT);
  pinMode(PIN_LED_YELLOW,  OUTPUT);
  pinMode(PIN_LED_RED,     OUTPUT);
  pinMode(PIN_LED_GREEN,   OUTPUT);
  pinMode(PIN_MOTOR_CTRL,  OUTPUT);

  // Tudo desligado no boot
  digitalWrite(LED_BUILTIN,    LOW);
  digitalWrite(PIN_LED_YELLOW, LOW);
  digitalWrite(PIN_LED_RED,    LOW);
  digitalWrite(PIN_LED_GREEN,  LOW);
  digitalWrite(PIN_MOTOR_CTRL, LOW);
}

// ════════════════════════════════════════════════════════════
//  WiFi
// ════════════════════════════════════════════════════════════
void setupWifi() {
  Serial.printf("[WiFi] Conectando a %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long t = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t < WIFI_TIMEOUT_MS) {
    delay(300);
    Serial.print(".");
    // Pisca LED builtin enquanto conecta
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiOk = true;
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.printf("\n[WiFi] OK · IP: %s · RSSI: %d dBm\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
#if USE_MDNS
    if (MDNS.begin("esp32-motor")) {
      Serial.println("[mDNS] Registrado como esp32-motor.local");
    }
#endif
  } else {
    wifiOk = false;
    digitalWrite(LED_BUILTIN, LOW);
    Serial.println("\n[WiFi] FALHOU — retry no proximo ciclo");
  }
}

void resolveHost() {
#if USE_MDNS
  String mdnsTarget = String(MDNS_HOST) + ".local";
  Serial.printf("[mDNS] Resolvendo %s...\n", mdnsTarget.c_str());
  IPAddress ip = MDNS.queryHost(mdnsTarget.c_str(), 3000);
  if ((uint32_t)ip != 0) {
    resolvedHost = ip.toString();
    Serial.printf("[mDNS] %s → %s\n", mdnsTarget.c_str(), resolvedHost.c_str());
    return;
  }
  Serial.println("[mDNS] Nao resolvido — usando IP fixo");
#endif
  resolvedHost = String(API_HOST);
  Serial.printf("[NET] Host: %s:%d\n", resolvedHost.c_str(), API_PORT);
}

// ════════════════════════════════════════════════════════════
//  SENSORES
// ════════════════════════════════════════════════════════════
float readTemperature() {
#if USE_DHT22
  float t = dht.readTemperature();
  if (isnan(t)) {
    Serial.println("[WARN] DHT22 falhou — usando 25.0C");
    return 25.0f;
  }
  return t;
#else
  // LM35: 10 mV/°C, ADC 12-bit, VREF 3.3V
  int raw = analogRead(PIN_TEMP_LM35);
  float voltage = (raw / 4095.0f) * ADC_VREF;
  return voltage * 100.0f;
#endif
}

float readVibration() {
#if USE_ADXL345
  sensors_event_t event;
  accel.getEvent(&event);
  float ax = event.acceleration.x;
  float ay = event.acceleration.y;
  float az = event.acceleration.z;
  // Magnitude da aceleração em m/s² convertida para mm/s (fator empírico)
  return sqrt(ax * ax + ay * ay + az * az) * 1.5f;
#else
  // SW-420: HIGH = vibração detectada
  return (digitalRead(PIN_VIBRATION) == HIGH) ? 15.0f : 2.0f;
#endif
}

float readCurrent() {
  // Média de CURRENT_SAMPLES amostras para reduzir ruído ADC
  long sum = 0;
  for (int i = 0; i < CURRENT_SAMPLES; i++) {
    sum += analogRead(PIN_CURRENT);
    delayMicroseconds(10);
  }
  float raw_avg = sum / (float)CURRENT_SAMPLES;
  float voltage  = (raw_avg / 4095.0f) * ADC_VREF;
  float current  = (voltage - ACS712_VCC_HALF) / ACS712_SENSITIVITY;
  return max(0.0f, current);
}

float readVoltage() {
  int   raw     = analogRead(PIN_VOLTAGE);
  float v_adc   = (raw / 4095.0f) * ADC_VREF;
  return v_adc * VOLTAGE_RATIO;
}

// ════════════════════════════════════════════════════════════
//  MOTOR + LEDs
// ════════════════════════════════════════════════════════════

// Controla o motor físico (BC547 via GPIO26) e atualiza LEDs
void setMotor(bool on) {
  if (on == motorRunning) return; // sem mudança

  motorRunning = on;
  digitalWrite(PIN_MOTOR_CTRL, on ? HIGH : LOW);
  updateLEDs();

  Serial.printf("[MOTOR] %s\n", on ? "LIGADO  → LED VERDE acesa" : "PARADO  → LED VERMELHA acesa");
}

void updateLEDs() {
  // Amarela: sempre acesa (gerenciada no setup e nunca apagada)
  digitalWrite(PIN_LED_GREEN, motorRunning ? HIGH : LOW);
  digitalWrite(PIN_LED_RED,   motorRunning ? LOW  : HIGH);
}

// ════════════════════════════════════════════════════════════
//  HTTP — POST leituras
// ════════════════════════════════════════════════════════════
void postReading() {
  float temp = readTemperature();
  float vib  = readVibration();
  float curr = readCurrent();
  float volt = readVoltage();

  StaticJsonDocument<256> doc;
  doc["temperature"] = serialized(String(temp, 2));
  doc["vibration"]   = serialized(String(vib,  2));
  doc["current"]     = serialized(String(curr, 2));
  doc["voltage"]     = serialized(String(volt, 2));
  doc["device_id"]   = DEVICE_ID;
  doc["source"]      = "esp32";

  String body;
  serializeJson(doc, body);

  String url = "http://" + resolvedHost + ":" + String(API_PORT) + String(API_ENDPOINT);

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(HTTP_TIMEOUT_MS);

  int code = http.POST(body);
  http.end();

  if (code == 200 || code == 201) {
    httpFailCount = 0;
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.printf("[OK]  T=%.1fC Vib=%.2fmm/s I=%.2fA U=%.2fV  motor=%s\n",
                  temp, vib, curr, volt, motorRunning ? "ON" : "OFF");
  } else {
    httpFailCount++;
    Serial.printf("[ERR] POST %d (falha consecutiva: %d)\n", code, httpFailCount);

    // Pisca LED builtin 3x para indicar falha de envio
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_BUILTIN, LOW);  delay(100);
      digitalWrite(LED_BUILTIN, HIGH); delay(100);
    }

    // Após 5 falhas, tenta redescobrir o host
    if (httpFailCount >= 5) {
      Serial.println("[NET] 5 falhas — redescobrir host...");
      resolveHost();
      httpFailCount = 0;
    }
  }
}

// ════════════════════════════════════════════════════════════
//  HTTP — GET estado do motor (polling do dashboard)
//
//  O dashboard chama POST /api/motor/start ou /api/motor/stop.
//  O backend grava is_running no banco.
//  A placa lê is_running aqui e controla GPIO26 + LEDs.
// ════════════════════════════════════════════════════════════
void pollMotorState() {
  String url = "http://" + resolvedHost + ":" + String(API_PORT) + String(API_HEALTH_PATH);

  HTTPClient http;
  http.begin(url);
  http.setTimeout(HTTP_TIMEOUT_MS);

  int code = http.GET();
  if (code == 200) {
    String payload = http.getString();
    StaticJsonDocument<256> doc;
    DeserializationError err = deserializeJson(doc, payload);

    if (!err && doc.containsKey("is_running")) {
      bool backendRunning = doc["is_running"].as<bool>();
      setMotor(backendRunning); // só age se houver mudança
    }
  } else {
    Serial.printf("[WARN] pollMotorState HTTP %d\n", code);
  }

  http.end();
}
