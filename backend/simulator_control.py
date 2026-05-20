"""
Controle do processo do simulador de sensores (subprocess).
"""
import os
import signal
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SIMULATOR_DIR = PROJECT_ROOT / "simulator"
SIMULATOR_SCRIPT = SIMULATOR_DIR / "simulate_sensors.py"

VALID_PROFILES = ("normal", "wear", "failure", "overload")
PROFILE_LABELS = {
    "normal": "Operação Normal",
    "wear": "Desgaste Progressivo",
    "failure": "Falha Iminente",
    "overload": "Sobrecarga Elétrica",
}

_proc: subprocess.Popen | None = None
_profile: str | None = None
_cycle: bool = False


def _script_exists() -> bool:
    return SIMULATOR_SCRIPT.is_file()


def _find_external_pid() -> int | None:
    try:
        out = subprocess.run(
            ["pgrep", "-f", "simulate_sensors.py"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if out.returncode == 0 and out.stdout.strip():
            return int(out.stdout.strip().split()[0])
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


def _managed_running() -> bool:
    global _proc
    if _proc is None:
        return False
    if _proc.poll() is not None:
        _proc = None
        return False
    return True


def get_status() -> dict:
    global _profile, _cycle
    if _managed_running():
        return {
            "running": True,
            "pid": _proc.pid,
            "profile": _profile,
            "cycle": _cycle,
            "managed_by_api": True,
            "profile_label": PROFILE_LABELS.get(_profile or "", _profile),
        }
    ext_pid = _find_external_pid()
    if ext_pid:
        return {
            "running": True,
            "pid": ext_pid,
            "profile": None,
            "cycle": None,
            "managed_by_api": False,
            "profile_label": "Iniciado externamente (start.sh)",
        }
    return {
        "running": False,
        "pid": None,
        "profile": None,
        "cycle": False,
        "managed_by_api": False,
        "profile_label": None,
    }


def _esp32_active() -> bool:
    """Placa enviando leituras recentes — não iniciar simulador."""
    try:
        from database import SessionLocal
        from data_source import esp32_sending_live

        db = SessionLocal()
        try:
            return esp32_sending_live(db)
        finally:
            db.close()
    except Exception:
        return False


def start_simulator(profile: str = "normal", cycle: bool = False) -> dict:
    global _proc, _profile, _cycle

    if not _script_exists():
        raise FileNotFoundError(f"Script não encontrado: {SIMULATOR_SCRIPT}")

    if profile not in VALID_PROFILES:
        raise ValueError(f"Perfil inválido: {profile}")

    if _esp32_active():
        raise RuntimeError(
            "Placa ESP32 enviando dados. Desligue a placa ou aguarde parar de enviar "
            "antes de ligar o simulador (use ./start.sh --real para modo só placa)."
        )

    st = get_status()
    if st["running"]:
        raise RuntimeError("Simulador já está em execução")

    cmd = [sys.executable, str(SIMULATOR_SCRIPT), "--profile", profile]
    if cycle:
        cmd.append("--cycle")

    _proc = subprocess.Popen(
        cmd,
        cwd=str(SIMULATOR_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    _profile = profile
    _cycle = cycle

    return {
        "ok": True,
        "pid": _proc.pid,
        "profile": profile,
        "cycle": cycle,
        "message": f"Simulador iniciado (perfil: {PROFILE_LABELS[profile]})",
    }


def stop_simulator() -> dict:
    global _proc, _profile, _cycle

    if _managed_running():
        try:
            os.killpg(os.getpgid(_proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            _proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(_proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        _proc = None
        _profile = None
        _cycle = False
        return {"ok": True, "message": "Simulador encerrado"}

    ext_pid = _find_external_pid()
    if ext_pid:
        try:
            os.kill(ext_pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        return {"ok": True, "message": "Simulador externo encerrado"}

    return {"ok": True, "message": "Simulador não estava em execução"}
