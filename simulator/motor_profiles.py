"""
Perfis de operação do motor para o simulador.
Cada perfil define curvas de temperatura, vibração e corrente ao longo do tempo.
"""
import math
import random

NOMINAL_CURRENT = 8.0   # A — corrente nominal de referência
NOMINAL_VOLTAGE = 380.0 # V — tensão trifásica


def _noise(amplitude: float = 0.02) -> float:
    """Ruído gaussiano leve para simular variação real de sensor."""
    return random.gauss(0, amplitude)


# ─── Perfil 1: Normal ─────────────────────────────────────────────────────────
def profile_normal(t: float) -> dict:
    """
    Operação normal dentro dos limites.
    t = tempo em segundos desde início do perfil.
    """
    temp    = 55.0 + 5 * math.sin(t / 120) + _noise(1.0)
    vib     = 8.0  + 2 * math.sin(t / 60)  + _noise(0.3)
    current = NOMINAL_CURRENT * (1.0 + 0.05 * math.sin(t / 30)) + _noise(0.1)
    voltage = NOMINAL_VOLTAGE + _noise(2.0)
    return dict(temperature=round(temp, 2), vibration=round(max(vib, 0), 2),
                current=round(current, 2), voltage=round(voltage, 1))


# ─── Perfil 2: Desgaste Progressivo ───────────────────────────────────────────
def profile_wear(t: float) -> dict:
    """
    Desgaste progressivo: temperatura e vibração sobem gradualmente.
    Simula rolamentos desgastados + superaquecimento gradual.
    """
    progress = min(t / 300, 1.0)   # 0→1 em 5 minutos

    temp    = 60.0 + progress * 22.0 + 3 * math.sin(t / 30) + _noise(1.5)
    vib     = 10.0 + progress * 18.0 + 2 * math.sin(t / 20) + _noise(0.5)
    current = NOMINAL_CURRENT * (1.0 + progress * 0.18) + _noise(0.2)
    voltage = NOMINAL_VOLTAGE - progress * 8 + _noise(2.0)

    return dict(temperature=round(temp, 2), vibration=round(max(vib, 0), 2),
                current=round(current, 2), voltage=round(voltage, 1))


# ─── Perfil 3: Falha Iminente ─────────────────────────────────────────────────
def profile_failure(t: float) -> dict:
    """
    Falha iminente: todos os parâmetros críticos.
    Temperatura > 85°C, vibração > 35 mm/s, corrente > 35% acima da nominal.
    """
    # Oscilações irregulares simulam instabilidade mecânica
    temp    = 88.0 + 4 * math.sin(t / 8)  + _noise(2.0)
    vib     = 38.0 + 5 * math.sin(t / 5)  + _noise(1.0)
    current = NOMINAL_CURRENT * 1.40 + 0.5 * math.sin(t / 10) + _noise(0.3)
    voltage = NOMINAL_VOLTAGE - 15 + 3 * math.sin(t / 7) + _noise(3.0)

    return dict(temperature=round(temp, 2), vibration=round(max(vib, 0), 2),
                current=round(current, 2), voltage=round(voltage, 1))


# ─── Perfil 4: Sobrecarga Elétrica ───────────────────────────────────────────
def profile_overload(t: float) -> dict:
    """
    Sobrecarga elétrica: corrente muito acima da nominal, temperatura moderada.
    """
    temp    = 68.0 + 3 * math.sin(t / 40) + _noise(1.0)
    vib     = 12.0 + 1.5 * math.sin(t / 25) + _noise(0.4)
    current = NOMINAL_CURRENT * (1.38 + 0.05 * math.sin(t / 15)) + _noise(0.2)
    voltage = NOMINAL_VOLTAGE - 10 + _noise(2.0)

    return dict(temperature=round(temp, 2), vibration=round(max(vib, 0), 2),
                current=round(current, 2), voltage=round(voltage, 1))


# ─── Registry ────────────────────────────────────────────────────────────────
PROFILES = {
    "normal":    profile_normal,
    "wear":      profile_wear,
    "failure":   profile_failure,
    "overload":  profile_overload,
}

PROFILE_DESCRIPTIONS = {
    "normal":   "Operação Normal",
    "wear":     "Desgaste Progressivo",
    "failure":  "Falha Iminente",
    "overload": "Sobrecarga Elétrica",
}
