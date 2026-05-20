#pragma once

// ═══════════════════════════════════════════════════════════
//  DEMANDA CONFIMINAS — Configuração do Firmware ESP32
//  Edite este arquivo com suas credenciais e endereços.
// ═══════════════════════════════════════════════════════════

// ─── WiFi ─────────────────────────────────────────────────
#define WIFI_SSID     "SUA_REDE_WIFI"
#define WIFI_PASSWORD "SUA_SENHA_WIFI"

// ─── Backend ──────────────────────────────────────────────
// IP do computador que roda o FastAPI (ifconfig / ipconfig)
#define API_HOST      "192.168.1.100"
#define API_PORT      8000
#define API_ENDPOINT  "/api/readings"

// ─── Intervalo de envio ────────────────────────────────────
#define SEND_INTERVAL_MS 2000   // 2 segundos

// ─── Pinos dos Sensores ───────────────────────────────────
// Temperatura — DHT22 ou LM35
#define PIN_TEMP_DHT    4       // GPIO4 — Data do DHT22
#define USE_DHT22       true    // true = DHT22 | false = LM35 (ADC)
#define PIN_TEMP_LM35   34      // GPIO34 (ADC) — apenas se USE_DHT22 = false

// Vibração — SW-420 (digital) ou ADXL345 (I2C)
#define USE_ADXL345     false   // true = ADXL345 I2C | false = SW-420 digital
#define PIN_VIBRATION   35      // GPIO35 — SW-420 (entrada digital)
// ADXL345 usa I2C: SDA=21, SCL=22 (padrão ESP32)

// Corrente — SCT-013 (via ADC + burden resistor)
#define PIN_CURRENT     32      // GPIO32 (ADC1) — saída do SCT-013
#define SCT_TURNS       2000    // Relação de espiras do SCT-013-030
#define BURDEN_OHMS     33.0f   // Resistor burden em ohms
#define ADC_VREF        3.3f    // Tensão de referência ADC
#define ADC_BITS        12      // Resolução ADC (12 bits = 0-4095)
#define CURRENT_SAMPLES 1000    // Amostras para cálculo RMS

// Tensão — Divisor resistivo (fase-neutro monofásico ou medição direta)
#define PIN_VOLTAGE     33      // GPIO33 (ADC1)
#define VOLTAGE_RATIO   110.0f  // Razão do divisor/transformador de tensão
// Ajuste: V_real = V_adc * (ADC_VREF / 4095) * VOLTAGE_RATIO

// Motor — Controle PWM/relé
#define PIN_MOTOR_CTRL  26      // GPIO26 — Relé ou MOSFET de controle
#define MOTOR_ON_LEVEL  HIGH    // Nível lógico para ligar o motor

// ─── Identificação ─────────────────────────────────────────
#define DEVICE_ID   "ESP32-MOTOR-01"
#define FIRMWARE_VER "1.0.0"
