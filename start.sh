#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  ConfiMinas — Motor Monitor · script de inicialização
#
#  Uso:
#    ./start.sh                       → simulador (perfil "normal")
#    ./start.sh --cycle               → simulador alternando perfis
#    ./start.sh --profile failure     → perfil específico
#    ./start.sh --real                → só backend (aguarda ESP32 real)
#    ./start.sh --no-sim              → alias de --real
#
#  Variáveis aceitas:
#    AUTH_USER      (default: master)
#    AUTH_PASS      (default: master)
#    AUTH_DISABLED  (default: false)  — true desativa autenticação
#    BACKEND_PORT   (default: 8000)
#    DASHBOARD_PORT (default: 3000)
# ═══════════════════════════════════════════════════════════════

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PROFILE="normal"
CYCLE=false
REAL_ESP32=false

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --cycle)         CYCLE=true ;;
    --real|--no-sim) REAL_ESP32=true ;;
    --profile)       PROFILE="${2:?--profile precisa de valor}"; shift ;;
    -h|--help)
      sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "Opção desconhecida: $1" >&2; exit 1 ;;
  esac
  shift
done

BACKEND_PORT="${BACKEND_PORT:-8000}"
DASHBOARD_PORT="${DASHBOARD_PORT:-3000}"
export AUTH_USER="${AUTH_USER:-Vinícius}"
export AUTH_PASS="${AUTH_PASS:-master}"
export AUTH_DISABLED="${AUTH_DISABLED:-false}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

printf '\n%b' "${CYAN}╔══════════════════════════════════════════════════╗${NC}\n"
printf '%b'   "${CYAN}║   ConfiMinas — Motor Monitor   v2.1.0            ║${NC}\n"
printf '%b'   "${CYAN}╚══════════════════════════════════════════════════╝${NC}\n\n"

# ── Dependências ─────────────────────────────────────────────
printf '%b' "${BLUE}[1/4]${NC} Verificando dependências...\n"
command -v node    >/dev/null || { printf '%b' "${RED}[ERR]${NC} Node.js não encontrado.\n";    exit 1; }
command -v python3 >/dev/null || { printf '%b' "${RED}[ERR]${NC} Python 3 não encontrado.\n"; exit 1; }

# pydantic-core requer Python 3.10–3.13 (algumas builds)
PYTHON_BIN=""
for c in python3.13 python3.12 python3.11 python3.10; do
  if command -v "$c" >/dev/null; then PYTHON_BIN="$c"; break; fi
done
[ -z "$PYTHON_BIN" ] && PYTHON_BIN="python3"
printf '%b' "${GREEN}[OK]${NC}  $PYTHON_BIN · Node $(node --version)\n"

# ── venv + pip ───────────────────────────────────────────────
printf '\n%b' "${BLUE}[2/4]${NC} Preparando ambiente Python...\n"
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  printf '%b' "${GREEN}[OK]${NC}  venv criado em .venv\n"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$SCRIPT_DIR/backend/requirements.txt"
printf '%b' "${GREEN}[OK]${NC}  dependências Python OK\n"

# ── npm ──────────────────────────────────────────────────────
printf '\n%b' "${BLUE}[3/4]${NC} Preparando dashboard...\n"
cd "$SCRIPT_DIR/dashboard"
if [ ! -d node_modules ]; then
  npm install --silent
fi
printf '%b' "${GREEN}[OK]${NC}  node_modules OK\n"

# ── Mata processos anteriores ────────────────────────────────
for p in "$BACKEND_PORT" "$DASHBOARD_PORT"; do
  pids="$(lsof -t -i:"$p" 2>/dev/null || true)"
  [ -n "$pids" ] && kill $pids 2>/dev/null || true
done
sleep 0.5

# ── Backend ──────────────────────────────────────────────────
printf '\n%b' "${BLUE}[4/4]${NC} Iniciando serviços...\n\n"
cd "$SCRIPT_DIR/backend"
printf '%b' "${GREEN}▶${NC} Backend FastAPI :$BACKEND_PORT\n"
uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload > /tmp/motor_backend.log 2>&1 &
BACKEND_PID=$!
sleep 3
if ! curl -sf "http://localhost:$BACKEND_PORT/api/health" >/dev/null; then
  printf '%b' "${RED}[ERR]${NC} backend não subiu — log:\n"
  tail -20 /tmp/motor_backend.log
  exit 1
fi
printf '%b' "${GREEN}[OK]${NC}  backend pronto (PID $BACKEND_PID)\n"

# ── Simulador ────────────────────────────────────────────────
SIM_PID=""
if [ "$REAL_ESP32" = false ]; then
  cd "$SCRIPT_DIR/simulator"
  if [ "$CYCLE" = true ]; then
    printf '%b' "${GREEN}▶${NC} Simulador (ciclo automático)\n"
    "$VENV_DIR/bin/python" simulate_sensors.py --cycle > /tmp/motor_simulator.log 2>&1 &
  else
    printf '%b' "${GREEN}▶${NC} Simulador (perfil: $PROFILE)\n"
    "$VENV_DIR/bin/python" simulate_sensors.py --profile "$PROFILE" > /tmp/motor_simulator.log 2>&1 &
  fi
  SIM_PID=$!
else
  printf '%b' "${YELLOW}[INFO]${NC} Modo ESP32 real — aguardando dados da placa\n"
fi

# ── Dashboard ────────────────────────────────────────────────
cd "$SCRIPT_DIR/dashboard"
printf '%b' "${GREEN}▶${NC} Dashboard Next.js :$DASHBOARD_PORT\n"
PORT="$DASHBOARD_PORT" NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT" \
  npm run dev > /tmp/motor_dashboard.log 2>&1 &
DASH_PID=$!
sleep 5
printf '%b' "${GREEN}[OK]${NC}  dashboard pronto (PID $DASH_PID)\n"

printf '\n%b' "${CYAN}╔══════════════════════════════════════════════════╗${NC}\n"
printf '%b'   "${CYAN}║  Sistema iniciado com sucesso                    ║${NC}\n"
printf '%b'   "${CYAN}╠══════════════════════════════════════════════════╣${NC}\n"
printf "${CYAN}║  Dashboard : ${GREEN}http://localhost:%-5s${CYAN}              ║${NC}\n" "$DASHBOARD_PORT"
printf "${CYAN}║  API docs  : ${GREEN}http://localhost:%-5s/docs${CYAN}         ║${NC}\n" "$BACKEND_PORT"
printf "${CYAN}║  Login     : ${YELLOW}%s / %s${CYAN}                      ║${NC}\n" "$AUTH_USER" "$AUTH_PASS"
if [ "$REAL_ESP32" = false ]; then
  printf "${CYAN}║  Modo      : ${YELLOW}Simulador (%s)${CYAN}                    ║${NC}\n" "$PROFILE"
else
  printf '%b'   "${CYAN}║  Modo      : ${GREEN}ESP32 Real${CYAN}                          ║${NC}\n"
fi
printf '%b' "${CYAN}╠══════════════════════════════════════════════════╣${NC}\n"
printf '%b' "${CYAN}║  Logs : tail -f /tmp/motor_backend.log           ║${NC}\n"
printf '%b' "${CYAN}║  Ctrl+C para encerrar tudo                       ║${NC}\n"
printf '%b' "${CYAN}╚══════════════════════════════════════════════════╝${NC}\n\n"

cleanup() {
  printf '\n%b' "${YELLOW}[STOP]${NC} Encerrando...\n"
  kill "$BACKEND_PID" 2>/dev/null || true
  [ -n "$SIM_PID" ] && kill "$SIM_PID" 2>/dev/null || true
  kill "$DASH_PID"   2>/dev/null || true
  printf '%b' "${GREEN}[OK]${NC} Encerrado.\n"
  exit 0
}
trap cleanup INT TERM
wait
