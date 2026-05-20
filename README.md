# ⚙️ Sistema de Manutenção Preditiva — CONFIMINAS

Sistema completo de monitoramento de motor com análise preditiva em tempo real,
dashboard web e geração automática de Ordens de Serviço em PDF.

## 🏗 Arquitetura

```
[ESP32 + Sensores] ──HTTP POST──► [FastAPI :8000] ──► [SQLite]
[Simulador Python] ──HTTP POST──►        │
                                          ▼
                                  [Next.js :3000]
                                          │
                                  [PDF OS Preditiva]
```

## 🚀 Início Rápido

```bash
# 1. Clone e entre na pasta
cd DEMANDA_CONFIMINAS2

# 2. Inicia tudo (backend + simulador + dashboard)
./start.sh

# 3. Acesse o dashboard
# http://localhost:3000
```

### Modos de execução

```bash
./start.sh                          # Simulador perfil "normal"
./start.sh --cycle                  # Simulador alterna perfis (demo completo)
./start.sh --profile failure        # Simula falha iminente imediatamente
./start.sh --profile wear           # Simula desgaste progressivo
./start.sh --real                   # Só backend — aguarda ESP32 real
```

## 📡 ESP32 — Dados Reais

Para usar com a placa e sensores reais:

1. Edite `firmware/esp32_motor_monitor/config.h`:
   ```cpp
   #define WIFI_SSID     "SUA_REDE"
   #define WIFI_PASSWORD "SUA_SENHA"
   #define API_HOST      "192.168.x.x"   // IP do seu PC
   ```

2. Grave o firmware via Arduino IDE ou PlatformIO (veja `firmware/README.md`)

3. Inicie o backend sem simulador:
   ```bash
   ./start.sh --real
   ```

4. O dashboard mostrará "📡 ESP32 Real" ao receber os primeiros dados.

## 🔌 Sensores e Pinos

| Sensor | Modelo | Pino ESP32 |
|--------|--------|------------|
| Temperatura | DHT22 | GPIO 4 |
| Vibração | SW-420 | GPIO 35 |
| Corrente | SCT-013-030 | GPIO 32 |
| Tensão | ZMPT101B / divisor | GPIO 33 |
| Controle motor | Relé | GPIO 26 |

> Veja `firmware/esp32_motor_monitor/README.md` para esquema de ligação detalhado.

## ⚠️ Limites de Alarme

| Parâmetro | Alerta | Crítico |
|-----------|--------|---------|
| Temperatura | > 75°C | > 85°C |
| Vibração | > 25 mm/s | > 35 mm/s |
| Corrente | ±20% nominal | ±35% nominal |

**Regra de geração de OS:**
- 1 sensor em estado crítico → OS gerada imediatamente
- 2+ sensores em alerta → OS gerada (prioridade alta)

## 📁 Estrutura de Arquivos

```
DEMANDA_CONFIMINAS2/
├── firmware/
│   └── esp32_motor_monitor/
│       ├── esp32_motor_monitor.ino   ← Firmware principal
│       ├── config.h                  ← ⚠️ Configure WiFi e IP aqui
│       └── README.md
├── backend/
│   ├── main.py                       ← FastAPI endpoints
│   ├── database.py                   ← Models SQLite
│   ├── predictive.py                 ← Lógica de análise preditiva
│   ├── service_order_gen.py          ← Geração de PDF
│   └── requirements.txt
├── simulator/
│   ├── simulate_sensors.py           ← Simulador de sensores
│   └── motor_profiles.py             ← Perfis de falha
├── dashboard/
│   ├── pages/index.js                ← Dashboard principal
│   └── components/                   ← Gráficos e cards
├── start.sh                          ← ⭐ Inicia tudo
└── README.md
```

## 🛠 Dependências

**Backend (Python)**
```bash
pip install fastapi uvicorn sqlalchemy weasyprint
```

**Dashboard (Node.js)**
```bash
cd dashboard && npm install
```

**Firmware (Arduino)**
- DHT sensor library (Adafruit)
- ArduinoJson
- Adafruit ADXL345 (se usar ADXL345)

## 📊 API — Principais Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/readings` | Recebe dados dos sensores |
| GET | `/api/readings?limit=60` | Histórico de leituras |
| GET | `/api/status` | Status atual + análise |
| GET | `/api/service-orders` | Lista de OS geradas |
| GET | `/api/service-orders/{id}/pdf` | Download do PDF |
| POST | `/api/motor/start` | Registra motor ligado |
| POST | `/api/motor/stop` | Registra motor parado |

Documentação interativa: http://localhost:8000/docs

## 🔧 Configuração da Corrente Nominal

A corrente nominal do motor é usada como referência para alarmes de corrente.
Configure via API ou diretamente no banco:

```bash
curl -X PUT http://localhost:8000/api/motor/config \
  -H "Content-Type: application/json" \
  -d '{"nominal_current": 8.0}'
```
