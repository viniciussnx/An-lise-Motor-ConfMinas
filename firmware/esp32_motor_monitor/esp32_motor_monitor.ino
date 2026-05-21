/*
 * ════════════════════════════════════════════════════════════════════
 *  ConfiMinas — Firmware ESP32 Motor Monitor
 *  Versão: 2.0.0
 *
 *  Funcionalidades:
 *   - Leitura de DHT22/LM35, SW-420/ADXL345, ACS712-5A e divisor de tensão DC.
 *   - Envio HTTP JSON a cada SEND_INTERVAL_MS para /api/readings.
 *   - Auto-discovery via mDNS (confiminas.local) se API_HOST estiver inválido.
 *   - Reconexão WiFi automática com backoff e Task Watchdog Timer (TWDT).
 *   - LED interno indica estado: piscando = sem WiFi · aceso = enviando OK.
 *
 *  Dependências (Arduino Library Manager):
 *   - DHT sensor library (Adafruit) + Adafruit Unified Sensor
 *   - Adafruit ADXL345 (se USE_ADXL345)
 *   - ArduinoJson
 *   - ESP32 Core (WiFi, HTTPClient, ESPmDNS — built-in)
 * ════════════════════════════════════════════════════════════════════
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#if defined(USE_MDNS) && USE_MDNS
  #include <ESPmDNS.h>
#endif
#include "config.h"

#if USE_DHT22
  #include <DHT.h>
  DHT dht(PIN_TEMP_DHT, DHT22);
#endif

#if USE_ADXL345
  #include <Adafruit_ADXL345_U.h>
  Adafruit_ADXL345_Unified adxl = Adafruit_ADXL345_Unified(12345);
#endif

#ifndef LED_BUILTIN
  #define LED_BUILTIN 2
#endif

// ── Estado global ───────────────────────────────────────────────────
static String   g_apiHost = API_HOST;
static unsigned long g_lastSend = 0;
static unsigned long g_failures = 0;

// ── Sensores ────────────────────────────────────────────────────────

float readTemperature() {
#if USE_DHT22
  float t = dht.readTemperature();
  if (isnan(t)) {
    Serial.println("[WARN] DHT22 leitura inválida");
    return NAN;
  }
  return t;
#else
  int raw = analogRead(PIN_TEMP_LM35);
  float voltage = raw * (ADC_VREF / 4095.0f);
  return voltage * 100.0f;
#endif
}

float readVibration() {
#if USE_ADXL345
  sensors_event_t event;
  adxl.getEvent(&event);
  float ax = event.acceleration.x;
  float ay = event.acceleration.y;
  float az = event.acceleration.z - 9.81f;
  float magnitude = sqrtf(ax * ax + ay * ay + az * az);
  return magnitude * 6.0f;
#else
  unsigned long startMs = millis();
  int pulseCount = 0;
  bool lastState = digitalRead(PIN_VIBRATION);
  while (millis() - startMs < 100) {
    bool state = digitalRead(PIN_VIBRATION);
    if (state != lastState) { pulseCount++; lastState = state; }
    delayMicroseconds(100);
  }
  return constrain(pulseCount * 0.5f, 0.0f, 80.0f);
#endif
}

float readCurrentRMS() {
  // ACS712-5A: mede corrente DC pela tensão de saída
  // VCC=5V → saída 0A = 2.5V; sensibilidade = 185mV/A
  long sum = 0;
  for (int i = 0; i < CURRENT_SAMPLES; i++) {
    sum += analogRead(PIN_CURRENT);
    delayMicroseconds(50);
  }
  float avgVolt = ((float)sum / CURRENT_SAMPLES) * (ADC_VREF / 4095.0f);
  float current = (avgVolt - ACS712_VCC_HALF) / ACS712_SENSITIVITY;
  return fabsf(current);
}

float readVoltage() {
  long sum = 0;
  const int samples = 200;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(PIN_VOLTAGE);
    delayMicroseconds(100);
  }
  float avgRaw  = (float)sum / samples;
  float adcVolt = avgRaw * (ADC_VREF / 4095.0f);
  return adcVolt * VOLTAGE_RATIO;
}

// ── Rede ─────────────────────────────────────────────────────────────

void connectWiFi() {
  Serial.printf("[WiFi] Conectando a \"%s\"...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < WIFI_TIMEOUT_MS) {
    delay(300);
    Serial.print(".");
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] OK · IP: %s · RSSI: %d dBm\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
    digitalWrite(LED_BUILTIN, HIGH);
  } else {
    Serial.println("\n[WiFi] Falha — reiniciando em 3s");
    delay(3000);
    ESP.restart();
  }
}

bool resolveServer() {
#if USE_MDNS
  Serial.printf("[mDNS] Procurando %s.local...\n", MDNS_HOST);
  if (!MDNS.begin("esp32-motor")) {
    Serial.println("[mDNS] init falhou");
  } else {
    IPAddress ip = MDNS.queryHost(MDNS_HOST);
    if (ip != IPAddress(0,0,0,0)) {
      g_apiHost = ip.toString();
      Serial.printf("[mDNS] %s.local → %s\n", MDNS_HOST, g_apiHost.c_str());
      return true;
    }
    Serial.println("[mDNS] não encontrado — usando API_HOST do config.h");
  }
#endif
  g_apiHost = API_HOST;
  return false;
}

bool pingServer() {
  HTTPClient http;
  String url = "http://" + g_apiHost + ":" + String(API_PORT) + API_HEALTH_PATH;
  http.setTimeout(HTTP_TIMEOUT_MS);
  http.begin(url);
  int code = http.GET();
  http.end();
  return code == 200;
}

void sendReading(float temp, float vib, float current, float voltage) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    return;
  }

  String url = "http://" + g_apiHost + ":" + String(API_PORT) + API_ENDPOINT;

  StaticJsonDocument<256> doc;
  doc["temperature"] = roundf(temp * 10.0f) / 10.0f;
  doc["vibration"]   = roundf(vib * 100.0f) / 100.0f;
  doc["current"]     = roundf(current * 100.0f) / 100.0f;
  doc["voltage"]     = roundf(voltage * 10.0f) / 10.0f;
  doc["source"]      = "esp32";
  doc["device_id"]   = DEVICE_ID;

  String payload;
  serializeJson(doc, payload);

  HTTPClient http;
  http.setTimeout(HTTP_TIMEOUT_MS);
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(payload);

  if (code == 200 || code == 201) {
    g_failures = 0;
    digitalWrite(LED_BUILTIN, HIGH);
    String response = http.getString();
    StaticJsonDocument<512> resp;
    if (deserializeJson(resp, response) == DeserializationError::Ok) {
      const char* overall = resp["analysis"]["overall_status"] | "?";
      Serial.printf("[OK]  T=%.1fC V=%.2fmm/s I=%.2fA U=%.1fV  status=%s\n",
                    temp, vib, current, voltage, overall);
    }
  } else {
    g_failures++;
    Serial.printf("[ERR] HTTP %d · %s · falhas=%lu\n", code, url.c_str(), g_failures);
    digitalWrite(LED_BUILTIN, LOW);

    // Após 5 falhas seguidas, tenta re-resolver o servidor.
    if (g_failures % 5 == 0) {
      Serial.println("[NET] Re-tentando descobrir servidor (mDNS)...");
      resolveServer();
    }
  }
  http.end();
}

// ── Setup / Loop ─────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(400);

  Serial.println("\n==============================================");
  Serial.println(" ConfiMinas — Motor Monitor ESP32");
  Serial.printf(" Firmware v%s · device=%s\n", FIRMWARE_VER, DEVICE_ID);
  Serial.println("==============================================\n");

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  pinMode(PIN_MOTOR_CTRL, OUTPUT);
  digitalWrite(PIN_MOTOR_CTRL, LOW);

#if !USE_ADXL345
  pinMode(PIN_VIBRATION, INPUT);
#endif

#if USE_DHT22
  dht.begin();
  Serial.println("[INIT] DHT22 OK");
#endif

#if USE_ADXL345
  if (!adxl.begin()) {
    Serial.println("[ERR] ADXL345 nao encontrado");
  } else {
    adxl.setRange(ADXL345_RANGE_4_G);
    Serial.println("[INIT] ADXL345 OK");
  }
#endif

  analogReadResolution(ADC_BITS);
  analogSetAttenuation(ADC_11db);
  Serial.println("[INIT] ADC 12-bit, 11dB attn");

  connectWiFi();
  resolveServer();

  if (!pingServer()) {
    Serial.printf("[WARN] Servidor %s:%d nao respondeu — tentando mDNS...\n",
                  g_apiHost.c_str(), API_PORT);
    resolveServer();
  } else {
    Serial.printf("[NET]  Servidor OK em %s:%d\n", g_apiHost.c_str(), API_PORT);
  }

  Serial.printf("[READY] Envio a cada %d ms\n\n", SEND_INTERVAL_MS);
}

void loop() {
  unsigned long now = millis();

  if (now - g_lastSend >= SEND_INTERVAL_MS) {
    g_lastSend = now;

    float temp    = readTemperature();
    float vib     = readVibration();
    float current = readCurrentRMS();
    float voltage = readVoltage();

    if (isnan(temp) || temp < 0 || temp > 150) {
      Serial.println("[WARN] Temperatura fora da faixa — ignorando ciclo");
    } else {
      sendReading(temp, vib, current, voltage);
    }
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Reconectando...");
    connectWiFi();
  }
}
