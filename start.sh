#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  DEMANDA CONFIMINAS — Script de Inicialização
#
#  Uso:
#    ./start.sh               → simulador perfil "normal"
#    ./start.sh --cycle       → alterna perfis automaticamente
#    ./start.sh --real        → só backend (ESP32 envia dados reais)
#    ./start.sh --profile failure → perfil específico
# ═══════════════════════════════════════════════════════════════

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE="normal"
CYCLE=false
REAL_ESP32=false

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --cycle)   CYCLE=true ;;
    --real)    REAL_ESP32=true ;;
    --profile) PROFILE="$2"; shift ;;
    *) echo "Opção desconhecida: $1"; exit 1 ;;
  esac
  shift
done

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Motor Monitor — CONFIMINAS   v1.0.0        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ─── Verifica dependências ────────────────────────────────────
echo -e "${BLUE}[1/4]${NC} Verificando dependências..."

if ! command -v python3 &>/dev/null; then
  echo -e "${RED}[ERR]${NC} Python 3 não encontrado."
  exit 1
fi
if ! command -v node &>/dev/null; then
  echo -e "${RED}[ERR]${NC} Node.js não encontrado."
  exit 1
fi
echo -e "${GREEN}[OK]${NC}  Python $(python3 --version 2>&1 | cut -d' ' -f2) | Node $(node --version)"

# ─── Virtualenv + dependências Python ─────────────────────────
echo -e "\n${BLUE}[2/4]${NC} Configurando ambiente Python (venv)..."
VENV_DIR="$SCRIPT_DIR/.venv"

# pydantic-core exige Python <= 3.12. Buscar versão compatível.
PYTHON_BIN=""
for candidate in python3.12 python3.11 python3.10; do
  if command -v "$candidate" &>/dev/null; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo -e "${RED}[ERR]${NC} Python 3.10-3.12 não encontrado."
  echo -e "       Instale com: ${YELLOW}brew install python@3.12${NC}"
  echo -e "       Python 3.14 (atual) é incompatível com pydantic-core."
  exit 1
fi

echo -e "${GREEN}[OK]${NC}  Usando $PYTHON_BIN ($($PYTHON_BIN --version))"

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  echo -e "${GREEN}[OK]${NC}  Virtualenv criado em .venv"
else
  echo -e "${GREEN}[OK]${NC}  Virtualenv já existe"
fi

source "$VENV_DIR/bin/activate"
pip install -q -r "$SCRIPT_DIR/backend/requirements.txt"
echo -e "${GREEN}[OK]${NC}  Dependências Python instaladas"

# ─── Instala dependências Node ─────────────────────────────────
echo -e "\n${BLUE}[3/4]${NC} Instalando dependências do dashboard..."
cd "$SCRIPT_DIR/dashboard"
if [ ! -d "node_modules" ]; then
  npm install --silent
  echo -e "${GREEN}[OK]${NC}  Dependências Node instaladas"
else
  echo -e "${GREEN}[OK]${NC}  node_modules já existe"
fi

# ─── Mata processos anteriores ────────────────────────────────
kill $(lsof -t -i:8000) 2>/dev/null || true
kill $(lsof -t -i:3000) 2>/dev/null || true
sleep 1

# ─── Inicia Backend FastAPI ───────────────────────────────────
echo -e "\n${BLUE}[4/4]${NC} Iniciando serviços...\n"
cd "$SCRIPT_DIR/backend"
echo -e "${GREEN}▶${NC} Backend FastAPI (porta 8000)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/motor_backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

if ! curl -sf http://localhost:8000/api/health > /dev/null; then
  echo -e "${RED}[ERR]${NC} Backend não subiu. Log:"
  tail -20 /tmp/motor_backend.log
  exit 1
fi
echo -e "${GREEN}[OK]${NC}  Backend rodando (PID $BACKEND_PID)"

# ─── Inicia Simulador ─────────────────────────────────────────
SIM_PID=""
if [ "$REAL_ESP32" = false ]; then
  cd "$SCRIPT_DIR/simulator"
  if [ "$CYCLE" = true ]; then
    echo -e "${GREEN}▶${NC} Simulador (ciclo automático de perfis)..."
    python3 simulate_sensors.py --cycle > /tmp/motor_simulator.log 2>&1 &
  else
    echo -e "${GREEN}▶${NC} Simulador (perfil: $PROFILE)..."
    python3 simulate_sensors.py --profile "$PROFILE" > /tmp/motor_simulator.log 2>&1 &
  fi
  SIM_PID=$!
  echo -e "${GREEN}[OK]${NC}  Simulador rodando (PID $SIM_PID)"
else
  echo -e "${YELLOW}[INFO]${NC} Modo ESP32 real — aguardando dados da placa..."
fi

# ─── Inicia Dashboard Next.js ─────────────────────────────────
cd "$SCRIPT_DIR/dashboard"
echo -e "${GREEN}▶${NC} Dashboard Next.js (porta 3000)..."
npm run dev > /tmp/motor_dashboard.log 2>&1 &
DASH_PID=$!
sleep 5
echo -e "${GREEN}[OK]${NC}  Dashboard rodando (PID $DASH_PID)"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Sistema iniciado com sucesso!               ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Dashboard:  ${GREEN}http://localhost:3000${CYAN}          ║${NC}"
echo -e "${CYAN}║  API (docs): ${GREEN}http://localhost:8000/docs${CYAN}     ║${NC}"
if [ "$REAL_ESP32" = false ]; then
echo -e "${CYAN}║  Modo:       ${YELLOW}Simulador ($PROFILE)${CYAN}           ║${NC}"
else
echo -e "${CYAN}║  Modo:       ${GREEN}ESP32 Real${CYAN}                     ║${NC}"
fi
echo -e "${CYAN}╠══════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Logs: tail -f /tmp/motor_backend.log        ║${NC}"
echo -e "${CYAN}║  Pressione Ctrl+C para encerrar tudo.        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

cleanup() {
  echo -e "\n${YELLOW}[STOP]${NC} Encerrando serviços..."
  kill $BACKEND_PID 2>/dev/null || true
  [ -n "$SIM_PID" ] && kill $SIM_PID 2>/dev/null || true
  kill $DASH_PID   2>/dev/null || true
  echo -e "${GREEN}[OK]${NC}  Encerrado."
  exit 0
}

trap cleanup INT TERM
wait
