#!/usr/bin/env python3
"""
Simulador de Sensores - DEMANDA CONFIMINAS
Substitui o ESP32 para demonstração sem hardware.

Uso:
  python simulate_sensors.py [--profile normal|wear|failure|overload] [--host localhost] [--port 8000]
  python simulate_sensors.py --cycle          # Alterna perfis automaticamente (demo completo)
  python simulate_sensors.py --interactive    # Permite trocar perfil pelo teclado
"""
import sys
import time
import argparse
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from motor_profiles import PROFILES, PROFILE_DESCRIPTIONS

API_URL = "http://localhost:8000/api/readings"


def post_reading(data: dict, api_url: str) -> bool:
    payload = json.dumps({**data, "source": "simulator"}).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            result = json.loads(resp.read())
            overall = result.get("analysis", {}).get("overall_status", "?")
            return True, overall
    except urllib.error.URLError as e:
        return False, str(e)


def run_simulator(
    profile_name: str = "normal",
    api_url: str = API_URL,
    interval: float = 2.0,
    cycle: bool = False,
    duration_per_profile: float = 120.0,
):
    """
    Envia dados simulados ao backend a cada `interval` segundos.

    Se `cycle=True`, alterna automaticamente entre perfis:
      normal (2 min) → wear (3 min) → failure (2 min) → overload (2 min) → repete
    """
    cycle_schedule = [
        ("normal",   120),
        ("wear",     180),
        ("failure",  120),
        ("overload", 120),
    ] if cycle else [(profile_name, float("inf"))]

    print(f"\n{'='*55}")
    print(f"  Simulador de Sensores - CONFIMINAS")
    print(f"  API: {api_url}")
    print(f"  Intervalo: {interval}s")
    if cycle:
        print(f"  Modo: Ciclo automático de perfis")
    else:
        print(f"  Perfil: {PROFILE_DESCRIPTIONS.get(profile_name, profile_name)}")
    print(f"{'='*55}\n")
    print("  Pressione Ctrl+C para encerrar.\n")

    t_global = 0.0

    for sched_profile, sched_duration in cycle_schedule * 999:
        fn = PROFILES[sched_profile]
        t_profile = 0.0
        profile_end = time.time() + sched_duration

        if cycle:
            print(f"\n[PERFIL] → {PROFILE_DESCRIPTIONS[sched_profile]}")

        while time.time() < profile_end:
            data = fn(t_profile)

            ok, status = post_reading(data, api_url)

            status_icon = {"normal": "✅", "alert": "⚠️ ", "critical": "🔴"}.get(status, "❓")
            conn_icon   = "📡" if ok else "❌"

            print(
                f"  {conn_icon} {status_icon} "
                f"T={data['temperature']:5.1f}°C  "
                f"V={data['vibration']:5.2f}mm/s  "
                f"I={data['current']:5.2f}A  "
                f"U={data['voltage']:5.1f}V  "
                f"[{PROFILE_DESCRIPTIONS.get(sched_profile, sched_profile)}]"
            )

            time.sleep(interval)
            t_profile += interval
            t_global  += interval

        if not cycle:
            break   # perfil único → loop infinito externo


def main():
    parser = argparse.ArgumentParser(description="Simulador de Sensores para Motor Monitor")
    parser.add_argument("--profile", default="normal",
                        choices=list(PROFILES.keys()),
                        help="Perfil de operação do motor")
    parser.add_argument("--host",    default="localhost", help="Host do backend")
    parser.add_argument("--port",    default=8000, type=int, help="Porta do backend")
    parser.add_argument("--interval", default=2.0, type=float, help="Intervalo entre envios (s)")
    parser.add_argument("--cycle",   action="store_true",
                        help="Alternar perfis automaticamente (demo)")
    args = parser.parse_args()

    api_url = f"http://{args.host}:{args.port}/api/readings"

    try:
        run_simulator(
            profile_name=args.profile,
            api_url=api_url,
            interval=args.interval,
            cycle=args.cycle,
        )
    except KeyboardInterrupt:
        print("\n\n  Simulador encerrado.\n")


if __name__ == "__main__":
    main()
