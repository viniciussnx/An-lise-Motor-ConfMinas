/*
 * ═══════════════════════════════════════════════════════════════════
 *  DEMANDA CONFIMINAS — Firmware ESP32 Motor Monitor
 *  Versão: 1.0.0
 *
 *  Sensores suportados:
 *    - Temperatura: DHT22 (padrão) ou LM35 (ADC)
 *    - Vibração:    SW-420 digital ou ADXL345 (I2C)
 *    - Corrente:    SCT-013 (ADC com cálculo RMS)
 *    - Tensão:      Divisor resistivo (ADC)
 *
 *  Dependências (instalar via Library Manager):
 *    - DHT sensor library (Adafruit)
 *    - Adafruit Unified Sensor
 *    - ADXL345 (Adafruit) — se USE_ADXL345 = true
 *    - ArduinoJson
 *    - WiFi (built-in ESP32)
 *    - HTTPClient (built-in ESP32)
 * ═══════════════════════════════════════════════════════════════════
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "config.h"

// ─── Includes condicionais de sensores ───────────────────────────────────────
#if USE_DHT22
  #include <DHT.h>
  DHT dht(PIN_TEMP_DHT, DHT22);
#endif

#if USE_ADXL345
  #include <Adafruit_ADXL345_U.h>
  Adafruit_ADXL345_Unified adxl = Adafruit_ADXL345_Unified(12345);
#endif

// ─── Variáveis globais ────────────────────────────────────────────────────────
unsigned long lastSendTime = 0;
bool motorRunning = false;

// ─── Funções de leitura dos sensores ─────────────────────────────────────────

float readTemperature() {
#if USE_DHT22
  float t = dht.readTemperature();
  if (isnan(t)) {
    Serial.println("[WARN] DHT22: leitura inválida");
    return -1.0f;
  }
  return t;
#else
  // LM35: 10mV/°C, leitura via ADC
  int raw = analogRead(PIN_TEMP_LM35);
  float voltage = raw * (ADC_VREF / 4095.0f);
  return voltage * 100.0f; // LM35: 10mV = 1°C
#endif
}

float readVibration() {
#if USE_ADXL345
  // ADXL345: converte aceleração em magnitude (aproxima mm/s via integração simples)
  sensors_event_t event;
  adxl.getEvent(&event);
  float ax = event.acceleration.x;
  float ay = event.acceleration.y;
  float az = event.acceleration.z - 9.81f; // remove gravidade do eixo Z
  float magnitude = sqrt(ax*ax + ay*ay + az*az);
  // Conversão empírica: 1 m/s² ≈ 6 mm/s (depende do sistema mecânico)
  return magnitude * 6.0f;
#else
  // SW-420: sensor digital de vibração
  // Conta pulsos em 100ms para estimar intensidade
  unsigned long startMs = millis();
  int pulseCount = 0;
  bool lastState = digitalRead(PIN_VIBRATION);

  while (millis() - startMs < 100) {
    bool state = digitalRead(PIN_VIBRATION);
    if (state != lastState) {
      pulseCount++;
      lastState = state;
    }
    delayMicroseconds(100);
  }
  // Escala: 0 pulsos = 0 mm/s, 100 pulsos ≈ 50 mm/s (calibre conforme seu sistema)
  return constrain(pulseCount * 0.5f, 0.0f, 80.0f);
#endif
}

float readCurrentRMS() {
  // SCT-013 com resistor burden — cálculo RMS por amostragem
  long sumSq = 0;
  int minVal = 4095, maxVal = 0;

  for (int i = 0; i < CURRENT_SAMPLES; i++) {
    int raw = analogRead(PIN_CURRENT);
    if (raw < minVal) minVal = raw;
    if (raw > maxVal) maxVal = raw;
  }

  // Centro da onda (biasing via divisor de tensão no circuito)
  int center = (minVal + maxVal) / 2;

  for (int i = 0; i < CURRENT_SAMPLES; i++) {
    int raw = analogRead(PIN_CURRENT);
    long diff = raw - center;
    sumSq += diff * diff;
    delayMicroseconds(50); // ~20kHz sampling
  }

  float rmsRaw    = sqrt((float)sumSq / CURRENT_SAMPLES);
  float rmsVolt   = rmsRaw * (ADC_VREF / 4095.0f);
  float currentA  = (rmsVolt / BURDEN_OHMS) * SCT_TURNS;

  return currentA;
}

float readVoltage() {
  // Divisor resistivo — lê tensão proporcional
  int samples = 200;
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(PIN_VOLTAGE);
    delayMicroseconds(100);
  }
  float avgRaw  = (float)sum / samples;
  float adcVolt = avgRaw * (ADC_VREF / 4095.0f);
  return adcVolt * VOLTAGE_RATIO;
}

// ─── Conexão WiFi ─────────────────────────────────────────────────────────────

void connectWiFi() {
  Serial.printf("[WiFi] Conectando a %s...\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] Conectado! IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n[WiFi] Falha na conexão. Reiniciando em 5s...");
    delay(5000);
    ESP.restart();
  }
}

// ─── Envio de dados ao backend ────────────────────────────────────────────────

void sendReading(float temp, float vib, float current, float voltage) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    return;
  }

  char url[128];
  snprintf(url, sizeof(url), "http://%s:%d%s", API_HOST, API_PORT, API_ENDPOINT);

  StaticJsonDocument<256> doc;
  doc["temperature"] = round(temp * 10.0f) / 10.0f;
  doc["vibration"]   = round(vib  * 100.0f) / 100.0f;
  doc["current"]     = round(current * 100.0f) / 100.0f;
  doc["voltage"]     = round(voltage * 10.0f) / 10.0f;
  doc["source"]      = "esp32";

  String payload;
  serializeJson(doc, payload);

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int code = http.POST(payload);

  if (code == 201 || code == 200) {
    String response = http.getString();
    StaticJsonDocument<512> resp;
    deserializeJson(resp, response);
    const char* overall = resp["analysis"]["overall_status"] | "?";
    Serial.printf("[OK] T=%.1f°C Vib=%.2fmm/s I=%.2fA U=%.1fV → %s\n",
                  temp, vib, current, voltage, overall);
  } else {
    Serial.printf("[ERR] HTTP %d — %s\n", code, url);
  }

  http.end();
}

// ─── Setup ────────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n╔════════════════════════════════════╗");
  Serial.println("║  Motor Monitor ESP32 — CONFIMINAS  ║");
  Serial.printf("║  Firmware v%s                 ║\n", FIRMWARE_VER);
  Serial.println("╚════════════════════════════════════╝\n");

  // Pino de controle do motor
  pinMode(PIN_MOTOR_CTRL, OUTPUT);
  digitalWrite(PIN_MOTOR_CTRL, LOW);

  // Vibração SW-420
#if !USE_ADXL345
  pinMode(PIN_VIBRATION, INPUT);
#endif

  // Inicializa DHT22
#if USE_DHT22
  dht.begin();
  Serial.println("[INIT] DHT22 inicializado");
#endif

  // Inicializa ADXL345
#if USE_ADXL345
  if (!adxl.begin()) {
    Serial.println("[ERR] ADXL345 não encontrado! Verifique I2C.");
  } else {
    adxl.setRange(ADXL345_RANGE_4_G);
    Serial.println("[INIT] ADXL345 inicializado");
  }
#endif

  // ADC
  analogReadResolution(ADC_BITS);
  analogSetAttenuation(ADC_11db); // permite leitura até ~3.3V

  Serial.println("[INIT] ADC configurado (12 bits, 11dB attenuation)");

  // WiFi
  connectWiFi();

  Serial.printf("\n[READY] Enviando leituras a cada %dms para %s:%d\n\n",
                SEND_INTERVAL_MS, API_HOST, API_PORT);
}

// ─── Loop principal ───────────────────────────────────────────────────────────

void loop() {
  unsigned long now = millis();

  if (now - lastSendTime >= SEND_INTERVAL_MS) {
    lastSendTime = now;

    // Ler todos os sensores
    float temp    = readTemperature();
    float vib     = readVibration();
    float current = readCurrentRMS();
    float voltage = readVoltage();

    // Validação básica
    if (temp < 0 || temp > 150) {
      Serial.println("[WARN] Temperatura fora da faixa, ignorando leitura.");
      return;
    }

    sendReading(temp, vib, current, voltage);
  }

  // Reconexão WiFi automática
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Conexão perdida. Reconectando...");
    connectWiFi();
  }
}
