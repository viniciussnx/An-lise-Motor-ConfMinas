# Firmware ESP32 — Motor Monitor

## Sensores Suportados

| Sensor | Modelo | Pino padrão | Config |
|--------|--------|-------------|--------|
| Temperatura | DHT22 | GPIO 4 | `USE_DHT22 true` |
| Temperatura (alt.) | LM35 | GPIO 34 (ADC) | `USE_DHT22 false` |
| Vibração | SW-420 | GPIO 35 | `USE_ADXL345 false` |
| Vibração (alt.) | ADXL345 | I2C SDA=21, SCL=22 | `USE_ADXL345 true` |
| Corrente | ACS712-5A | GPIO 32 (ADC) | — |
| Tensão | Divisor R (R1=R2=10kΩ) | GPIO 33 (ADC) | `VOLTAGE_RATIO` |
| Motor | Transistor BC547 | GPIO 26 | — |
| LED WiFi | LED interno | GPIO 2 (LED_BUILTIN) | piscando = sem WiFi · aceso = enviando OK |
| LED Amarelo | LED 5mm | GPIO 25 | sempre acesa — circuito energizado |
| LED Vermelho | LED 5mm | GPIO 27 | motor parado |
| LED Verde | LED 5mm | GPIO 14 | motor em funcionamento |

## Auto-Discovery (mDNS)

Com `USE_MDNS true` em `config.h`, o firmware tenta resolver `confiminas.local`
antes de cair para `API_HOST`. Após 5 falhas HTTP seguidas a placa também
retenta o descobrimento. Isso evita reflashar quando o IP do servidor muda.

## Configuração rápida

1. **Painel web → Hardware → "Configurar Placa ESP32"** já mostra o IP correto
   do servidor e oferece **Baixar config.h** com o `API_HOST` pré-preenchido.
2. Edite somente `WIFI_SSID` / `WIFI_PASSWORD`.
3. Grave o firmware (Arduino IDE ou PlatformIO).

## Circuito ACS712-5A (Corrente DC)

```
ESP32 VIN (5V) ──→ ACS712 VCC
ESP32 GND      ──→ ACS712 GND
Fio do motor   ──→ ACS712 IP+ / IP-  (corrente passa pelos pinos)
ACS712 OUT     ──→ GPIO 32
```
- Capacitor 100nF entre OUT e GND reduz ruído ADC.
- Corrente máxima segura: 5A. Motor DC hobby tipicamente < 1A.

## Tensão DC (divisor resistivo)

```
Motor VCC (5V) ──→ R1 (10kΩ) ──→ GPIO 33
                                └── R2 (10kΩ) ──→ GND
```
- `VOLTAGE_RATIO = 2.0` → lê tensões DC até 6.6V.
- Capacitor 100nF entre GPIO33 e GND estabiliza a leitura.

## Controle do Motor (transistor BC547)

```
GPIO 26 ──→ R1 (1kΩ) ──→ BC547 Base
                          BC547 Coletor ──→ Motor DC (-)
Motor DC (+) ──→ VIN (5V)
BC547 Emissor ──→ GND
Diodo 1N4007 em paralelo com motor (catodo no +)
```

## Circuito dos LEDs de Status

Cada LED precisa de um resistor de 330Ω em série para limitar corrente (~10mA):

```
GPIO25 (Amarelo) ──→ 330Ω ──→ LED Amarelo ──→ GND
GPIO27 (Vermelho) ─→ 330Ω ──→ LED Vermelho ──→ GND
GPIO14 (Verde) ───→ 330Ω ──→ LED Verde ──→ GND
```

| LED | GPIO | Condição |
|-----|------|----------|
| Amarelo | 25 | Sempre acesa após energizar o circuito |
| Vermelho | 27 | Motor parado (padrão ao ligar) |
| Verde | 14 | Motor em funcionamento |

## Fluxo Dashboard → Motor → LEDs

```
Dashboard clica "Parar Motor"
  → POST /api/motor/stop
    → backend grava is_running=false no banco
      → ESP32 faz GET /api/esp32/health a cada 2s
        → lê is_running=false
          → GPIO26 = LOW (motor desliga)
          → LED Vermelho = HIGH
          → LED Verde    = LOW
```

## Gravação do Firmware

### Arduino IDE
1. Arquivo → Preferências → URLs adicionais:
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
2. Ferramentas → Placa → ESP32 → **ESP32 Dev Module**
3. Bibliotecas: `DHT sensor library`, `ArduinoJson`, `Adafruit ADXL345` (se usar I2C)
4. Edite `config.h` (apenas WiFi)
5. Compile e grave (Upload)

### PlatformIO
```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
lib_deps =
    adafruit/DHT sensor library
    bblanchon/ArduinoJson
    adafruit/Adafruit ADXL345
```

## Verificação pelo Serial Monitor (115200)

```
[WiFi] OK · IP: 192.168.1.105 · RSSI: -54 dBm
[mDNS] confiminas.local → 192.168.1.20
[NET]  Servidor OK em 192.168.1.20:8000
[READY] Envio a cada 2000 ms

[OK]  T=58.3C V=9.45mm/s I=7.89A U=381.2V  status=normal
[OK]  T=58.7C V=9.62mm/s I=7.95A U=380.8V  status=normal
```
