# Firmware ESP32 — Motor Monitor

## Sensores Suportados

| Sensor | Modelo | Pino padrão | Config |
|--------|--------|-------------|--------|
| Temperatura | DHT22 | GPIO 4 | `USE_DHT22 true` |
| Temperatura (alt.) | LM35 | GPIO 34 (ADC) | `USE_DHT22 false` |
| Vibração | SW-420 | GPIO 35 | `USE_ADXL345 false` |
| Vibração (alt.) | ADXL345 | I2C SDA=21, SCL=22 | `USE_ADXL345 true` |
| Corrente | SCT-013-030 | GPIO 32 (ADC) | — |
| Tensão | Divisor R | GPIO 33 (ADC) | `VOLTAGE_RATIO` |
| Motor | Relé/MOSFET | GPIO 26 | — |

## Circuito SCT-013 (Corrente)

```
SCT-013 saída (pin 1) ──┬── Resistor burden (33Ω) ── GND
                         └── GPIO 32 do ESP32
```
- Use um capacitor de 10µF entre GPIO32 e GND para estabilizar a leitura.
- O burden de 33Ω dá fundo de escala ≈ 30A (padrão SCT-013-030).

## Divisor de Tensão (Tensão da rede)

> ⚠️ **ATENÇÃO**: Nunca conecte a rede elétrica diretamente ao ESP32.
> Use um transformador de potencial (TP) ou módulo ZMPT101B.

**Com ZMPT101B (recomendado):**
```
Rede → ZMPT101B → Saída analógica → GPIO 33 + capacitor 100nF → GND
```
Ajuste `VOLTAGE_RATIO` conforme calibração do módulo.

## Gravação do Firmware

### Arduino IDE
1. Instale o suporte ESP32: Arquivo → Preferências → URLs adicionais:
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
2. Ferramentas → Placa → ESP32 → **ESP32 Dev Module**
3. Instale as bibliotecas: DHT sensor library, ArduinoJson, Adafruit ADXL345
4. Edite `config.h` com seus dados de WiFi e IP do servidor
5. Compile e grave (Upload)

### PlatformIO (VSCode)
```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    adafruit/DHT sensor library
    bblanchon/ArduinoJson
    adafruit/Adafruit ADXL345
```

## Configuração mínima no config.h

```cpp
#define WIFI_SSID     "NOME_DA_SUA_REDE"
#define WIFI_PASSWORD "SENHA_DA_REDE"
#define API_HOST      "192.168.x.x"   // IP do PC com o backend
```

## Verificação

Abra o Monitor Serial (115200 baud) após gravar. Você verá:
```
[WiFi] Conectado! IP: 192.168.1.105
[INIT] DHT22 inicializado
[READY] Enviando leituras a cada 2000ms

[OK] T=58.3°C Vib=9.45mm/s I=7.89A U=381.2V → normal
[OK] T=58.7°C Vib=9.62mm/s I=7.95A U=380.8V → normal
```
