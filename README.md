# ConfiMinas — Sistema de Manutenção Preditiva

Monitoramento de motor com análise preditiva em tempo real, dashboard web
autenticado e geração automática de Ordens de Serviço em PDF.

## Arquitetura

```
[ESP32 + sensores] ──HTTP POST──► [FastAPI :8000] ──► [SQLite WAL]
[Simulador Python] ──HTTP POST──►        │
                                          ▼
                          [Next.js :3000 · login + dashboard]
                                          │
                                  [PDF OS Preditiva]
```

## Início rápido

```bash
./start.sh                          # simulador "normal"
./start.sh --cycle                  # alterna perfis
./start.sh --profile failure        # falha iminente
./start.sh --real                   # só backend (aguarda ESP32 real)
```

Abrir `http://localhost:3000` → login com **master / master**.

### Credenciais

Padrão: `master / master`. Sobrescreva via variáveis de ambiente:

```bash
AUTH_USER=admin AUTH_PASS='senha-forte' ./start.sh
AUTH_DISABLED=true ./start.sh        # dev: sem autenticação
```

## ESP32 — Placa real

1. Painel web → **Hardware → Configurar Placa ESP32 → Baixar config.h**
   (já vem com o IP do servidor preenchido).
2. Em `config.h`, edite apenas `WIFI_SSID` e `WIFI_PASSWORD`.
3. Grave o firmware (Arduino IDE ou PlatformIO).
4. Inicie o backend em modo placa: `./start.sh --real`.
5. Quando a placa enviar dados, o card "ESP32" do painel passa para **Conectada**.

Auto-discovery via mDNS (`confiminas.local`) reduz dor de cabeça quando o IP do
servidor muda — o firmware tenta resolver o hostname antes do fallback do
`API_HOST` em `config.h`.

## Sensores e pinos

| Sensor | Modelo | Pino ESP32 |
|--------|--------|------------|
| Temperatura | DHT22 | GPIO 4 |
| Vibração | SW-420 / ADXL345 | GPIO 35 (ou I2C) |
| Corrente | SCT-013-030 | GPIO 32 |
| Tensão | ZMPT101B / divisor | GPIO 33 |
| Relé motor | — | GPIO 26 |

## Limites de alarme (padrão)

| Parâmetro | Alerta | Crítico |
|-----------|--------|---------|
| Temperatura | > 75 °C | > 85 °C |
| Vibração | > 25 mm/s | > 35 mm/s |
| Corrente | ±20 % nominal | ±35 % nominal |

Configuráveis em tempo de execução em **Limites** (frontend) ou via
`PUT /api/thresholds` (backend).

## Regra de geração de OS
- 1+ sensor em **crítico** → OS imediata (prioridade *crítica*)
- 2+ sensores em **alerta** → OS preventiva (prioridade *alta*)

## Estrutura de arquivos

```
DEMANDA_CONFIMINAS/
├── firmware/esp32_motor_monitor/    ESP32 (.ino + config.h)
├── backend/                         FastAPI + SQLite + PDF
│   ├── main.py                      endpoints + lifespan
│   ├── auth.py                      login HMAC (master/master)
│   ├── database.py                  modelos + WAL
│   ├── readings_service.py          ingestão unificada
│   ├── predictive.py                regras de alarme
│   ├── service_order_gen.py         PDF (ReportLab)
│   └── requirements.txt
├── simulator/                       gerador de leituras
├── dashboard/                       Next.js 14 + React 18
│   ├── pages/login.js               tela de acesso
│   ├── pages/index.js               dashboard principal
│   ├── pages/hardware.js            painel hardware/ESP32
│   ├── pages/thresholds.js          ajuste de limites
│   ├── lib/api.js                   cliente HTTP + sessão
│   └── components/                  gráficos, cards, OS
├── start.sh                         inicialização completa
└── README.md
```

## API — principais endpoints

| Método | Endpoint | Autenticação | Descrição |
|--------|----------|--------------|-----------|
| POST  | `/api/auth/login` | — | login (`username`,`password`) |
| GET   | `/api/auth/me`    | Bearer | usuário corrente |
| POST  | `/api/readings`   | — | recebe dados da placa/simulador |
| GET   | `/api/readings`   | Bearer | histórico |
| GET   | `/api/status`     | Bearer | estado atual |
| GET   | `/api/service-orders` | Bearer | lista de OS |
| GET   | `/api/service-orders/{id}/pdf` | Bearer | PDF da OS |
| PUT   | `/api/thresholds` | Bearer | atualiza limites |
| GET   | `/api/esp32/config` | — | template `config.h` |
| GET   | `/api/health`     | — | health-check |

Documentação interativa: `http://localhost:8000/docs`

## Configuração da corrente nominal

```bash
curl -X PUT http://localhost:8000/api/motor/config \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"nominal_current": 8.0}'
```

## Performance

- SQLite em modo **WAL** + `synchronous=NORMAL` (leituras concorrentes ao gravar).
- Índice composto `(source, timestamp)` em `sensor_readings`.
- Dashboard: polling 4 s, React memoization (componentes e `useMemo`).
- Imagens estáticas servidas com `unoptimized` (zero overhead em dev local).
