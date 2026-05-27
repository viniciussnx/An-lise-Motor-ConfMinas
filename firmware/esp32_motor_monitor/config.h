#pragma once

// ════════════════════════════════════════════════════════════
//  ConfiMinas — Configuração do Firmware ESP32
//  Edite as 3 linhas marcadas com [EDITAR].
// ════════════════════════════════════════════════════════════

// ── WiFi ────────────────────────────────────────────────────  [EDITAR]
#define WIFI_SSID     "SUA_REDE_WIFI"
#define WIFI_PASSWORD "SUA_SENHA_WIFI"

// ── Backend ─────────────────────────────────────────────────  [EDITAR]
// Coloque o IP do PC que roda o servidor (ifconfig / ipconfig).
// Se USE_MDNS=true, a placa também tenta resolver "confiminas.local".
#define API_HOST          "192.168.1.100"
#define API_PORT          8000
#define API_ENDPOINT      "/api/readings"
#define API_HEALTH_PATH   "/api/esp32/health"

// Auto-discovery via mDNS — fallback quando o IP estiver errado.
#define USE_MDNS          true
#define MDNS_HOST         "confiminas"          // → confiminas.local

// ── Envio ───────────────────────────────────────────────────
#define SEND_INTERVAL_MS  2000     // periodicidade de envio (ms)
#define HTTP_TIMEOUT_MS   4000
#define WIFI_TIMEOUT_MS   12000

// ── Temperatura ─────────────────────────────────────────────
#define PIN_TEMP_DHT      4        // GPIO4 — DHT22 DATA
#define USE_DHT22         true     // true=DHT22 | false=LM35
#define PIN_TEMP_LM35     34       // GPIO34 (ADC)

// ── Vibração ────────────────────────────────────────────────
#define USE_ADXL345       false    // true=ADXL345 I2C | false=SW-420 digital
#define PIN_VIBRATION     35       // GPIO35 (SW-420)

// ── Corrente — Potenciômetro 10kΩ (simulação) ───────────────
// Conexão: 3.3V → pot pino1 | GND → pot pino3 | cursor → GPIO32
// Gira pot: 0V=0A  1.65V=2.5A  3.3V=5A
#define PIN_CURRENT          32       // GPIO32 (ADC1)
#define ACS712_SENSITIVITY   0.66f    // 3.3V ÷ 5A (mapeamento pot→corrente)
#define ACS712_VCC_HALF      0.0f     // pot começa em 0V, sem offset
#define ADC_VREF             3.3f
#define ADC_BITS             12
#define CURRENT_SAMPLES      1000

// ── Tensão — divisor resistivo DC (R1=R2=10kΩ) ─────────────
#define PIN_VOLTAGE          33       // GPIO33 (ADC1)
#define VOLTAGE_RATIO        2.0f     // lê até 6.6V DC

// ── Motor (transistor BC547) ────────────────────────────────
#define PIN_MOTOR_CTRL    26
#define MOTOR_ON_LEVEL    HIGH

// ── LEDs de status ──────────────────────────────────────────
// Conexão: GPIO → Resistor 330Ω → LED → GND
#define PIN_LED_YELLOW    25   // GPIO25 — circuito energizado (sempre acesa)
#define PIN_LED_RED       27   // GPIO27 — motor parado
#define PIN_LED_GREEN     14   // GPIO14 — motor em funcionamento

// ── Identificação ───────────────────────────────────────────
#define DEVICE_ID    "ESP32-MOTOR-01"
#define FIRMWARE_VER "2.1.0"
