# 📡 Guia Completo — ESP32 com Sensores Reais

## 1. Componentes necessários

| Componente | Modelo | Finalidade |
|------------|--------|------------|
| Microcontrolador | ESP32 Dev Module | Leitura e envio de dados |
| Temperatura | DHT22 | Temperatura e umidade |
| Vibração | SW-420 | Detecção digital de vibração |
| Corrente | SCT-013-030 | Corrente RMS (não invasivo) |
| Tensão | ZMPT101B | Tensão AC (isolado) |
| Relé | Módulo Relé 5V | Controle on/off do motor |
| Resistores | 33Ω (burden), 10kΩ | Circuito SCT-013 |
| Capacitor | 10µF | Estabilização ADC |

---

## 2. Esquema de Ligação

### DHT22 (Temperatura)
```
DHT22 VCC  → 3.3V ESP32
DHT22 DATA → GPIO 4   (+ resistor pull-up 10kΩ para 3.3V)
DHT22 GND  → GND ESP32
```

### SW-420 (Vibração)
```
SW-420 VCC  → 3.3V ESP32
SW-420 DO   → GPIO 35
SW-420 GND  → GND ESP32
```

### SCT-013-030 (Corrente — não invasivo)
```
SCT-013 pino 1 → Nó A
SCT-013 pino 2 → Nó B

Nó A ─── Resistor 33Ω ─── GND
Nó A ─── GPIO 32 ESP32
Nó B ─── GND

Capacitor 10µF entre GPIO32 e GND (estabilização)
Divisor de tensão: 2x 10kΩ de 3.3V→GND, ponto médio → GPIO 32
(Fornece DC bias de 1.65V para leitura AC)
```

### ZMPT101B (Tensão)
```
ZMPT101B entrada → Fase L + Neutro N (110V/220V)
ZMPT101B saída   → GPIO 33 ESP32 + GND
⚠ Sempre use o módulo ZMPT101B completo (já tem isolamento galvânico)
```

### Relé (Controle do motor)
```
Relé VCC  → 5V (ou Vin do ESP32)
Relé IN   → GPIO 26
Relé GND  → GND ESP32
Relé COM  → Fase da rede (motor)
Relé NO   → Terminal do motor
```

---

## 3. Configuração do Firmware

### Passo 1 — Instalar Arduino IDE
Baixe em: https://www.arduino.cc/en/software

### Passo 2 — Adicionar suporte ao ESP32
1. Arduino IDE → Arquivo → Preferências
2. Cole em "URLs adicionais":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Ferramentas → Gerenciador de Placas → busque "esp32" → Instale "esp32 by Espressif"

### Passo 3 — Instalar bibliotecas
Ferramentas → Gerenciar Bibliotecas → instale:
- `DHT sensor library` (by Adafruit)
- `Adafruit Unified Sensor`
- `ArduinoJson` (by Benoit Blanchon)
- `Adafruit ADXL345` (se usar ADXL345 no lugar do SW-420)

### Passo 4 — Editar config.h
Abra `firmware/esp32_motor_monitor/config.h` e altere:

```cpp
#define WIFI_SSID     "NOME_DA_SUA_REDE_WIFI"
#define WIFI_PASSWORD "SENHA_DA_SUA_REDE"
#define API_HOST      "192.168.X.X"   // ← IP do seu computador
```

**Como saber seu IP?**
- Mac/Linux: `ifconfig | grep "inet " | grep -v 127`
- Windows: `ipconfig` → "Endereço IPv4"

### Passo 5 — Selecionar placa e porta
1. Ferramentas → Placa → ESP32 Arduino → **ESP32 Dev Module**
2. Ferramentas → Porta → selecione a porta USB do ESP32 (ex: /dev/cu.usbserial-0001 no Mac)
3. Ferramentas → Upload Speed → 115200

### Passo 6 — Gravar o firmware
1. Abra o arquivo `esp32_motor_monitor.ino`
2. Clique em **Upload** (→ seta para direita)
3. Se der erro "Failed to connect": segure o botão **BOOT** da placa enquanto o upload inicia

---

## 4. Iniciar o sistema com ESP32 real

```bash
# No computador, dentro da pasta do projeto:
./start.sh --real
```

Isso sobe o backend + dashboard sem o simulador.
O ESP32 enviará dados automaticamente a cada 2 segundos.

---

## 5. Verificação no Monitor Serial

Abra Arduino IDE → Ferramentas → Monitor Serial (115200 baud):

```
╔════════════════════════════════════╗
║  Motor Monitor ESP32 — CONFIMINAS  ║
║  Firmware v1.0.0                   ║
╚════════════════════════════════════╝

[WiFi] Conectando a MinhaRede...
[WiFi] Conectado! IP: 192.168.1.105
[INIT] DHT22 inicializado
[INIT] ADC configurado
[READY] Enviando leituras a cada 2000ms

[OK] T=58.3°C Vib=9.45mm/s I=7.89A U=381.2V → normal
[OK] T=58.7°C Vib=9.62mm/s I=7.95A U=380.8V → normal
```

---

## 6. Painel de Hardware (dashboard)

Acesse **http://localhost:3000/hardware**

O painel mostra:
- Status de conexão do ESP32 (Online/Offline)
- Valores em tempo real de cada sensor
- Indicação se os dados vêm do ESP32 real ou do simulador
- Guia de pinos para verificar conexões

---

## 7. Solução de Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| "Failed to connect to ESP32" | Botão BOOT não pressionado | Segure BOOT durante upload |
| Temperatura -1 ou NaN | DHT22 mal conectado | Verifique pull-up 10kΩ no DATA |
| Corrente sempre 0 | SCT-013 sem burden resistor | Adicione 33Ω entre os terminais |
| WiFi não conecta | SSID/senha errados | Revise config.h |
| API não responde | IP errado em config.h | Verifique com `ifconfig` |
| Vibração sem variação | SW-420 saturado | Ajuste o trimpot no módulo |

---

## 8. Calibração dos Sensores

### SCT-013 (Corrente)
Com um amperímetro de referência:
1. Meça a corrente real com o amperímetro
2. Leia o valor no dashboard
3. Ajuste `SCT_TURNS` em config.h até coincidir

### ZMPT101B (Tensão)
1. Meça a tensão real com multímetro
2. Ajuste `VOLTAGE_RATIO` em config.h proporcionalmente

---

## 9. Thresholds — Alterar valores de alarme

Acesse **http://localhost:3000/thresholds** no dashboard para configurar:
- Limite de Alerta e Crítico de temperatura
- Limite de Alerta e Crítico de vibração
- Corrente nominal do motor
- Percentual de desvio para alerta/crítico de corrente

Os valores são aplicados imediatamente via API sem reiniciar o sistema.
