"""
Lógica de análise preditiva para monitoramento de motor.
Avalia leituras dos sensores e determina alertas e ordens de serviço.
"""
import json
from dataclasses import dataclass
from typing import List, Tuple

# ─── Thresholds configuráveis ────────────────────────────────────────────────
TEMP_ALERT    = 75.0   # °C
TEMP_CRITICAL = 85.0   # °C

VIB_ALERT    = 25.0    # mm/s
VIB_CRITICAL = 35.0    # mm/s

CURRENT_ALERT_PCT    = 0.20   # ±20% da corrente nominal
CURRENT_CRITICAL_PCT = 0.35   # ±35% da corrente nominal


@dataclass
class SensorStatus:
    temperature: float
    vibration: float
    current: float
    voltage: float
    nominal_current: float

    temp_status: str = "normal"
    vib_status: str = "normal"
    current_status: str = "normal"
    anomalies: List[str] = None
    suggested_actions: List[str] = None
    should_generate_os: bool = False
    priority: str = "normal"

    def __post_init__(self):
        self.anomalies = []
        self.suggested_actions = []


def evaluate_temperature(temp: float) -> Tuple[str, str, str]:
    """Retorna (status, anomalia, ação)"""
    if temp >= TEMP_CRITICAL:
        return (
            "critical",
            f"Temperatura crítica: {temp:.1f}°C (limite crítico: {TEMP_CRITICAL}°C)",
            "Desligar motor imediatamente e verificar sistema de resfriamento/ventilação"
        )
    elif temp >= TEMP_ALERT:
        return (
            "alert",
            f"Temperatura elevada: {temp:.1f}°C (limite de alerta: {TEMP_ALERT}°C)",
            "Inspecionar ventilação, filtros e rolamentos por superaquecimento"
        )
    return ("normal", None, None)


def evaluate_vibration(vib: float) -> Tuple[str, str, str]:
    """Retorna (status, anomalia, ação)"""
    if vib >= VIB_CRITICAL:
        return (
            "critical",
            f"Vibração crítica: {vib:.2f} mm/s (limite crítico: {VIB_CRITICAL} mm/s)",
            "Parar motor e realizar alinhamento/balanceamento urgente"
        )
    elif vib >= VIB_ALERT:
        return (
            "alert",
            f"Vibração elevada: {vib:.2f} mm/s (limite de alerta: {VIB_ALERT} mm/s)",
            "Inspecionar rolamentos, acoplamento e alinhamento do eixo"
        )
    return ("normal", None, None)


def evaluate_current(current: float, nominal: float) -> Tuple[str, str, str]:
    """Retorna (status, anomalia, ação)"""
    deviation = abs(current - nominal) / nominal

    if deviation >= CURRENT_CRITICAL_PCT:
        direction = "acima" if current > nominal else "abaixo"
        return (
            "critical",
            f"Corrente fora do limite crítico: {current:.2f}A ({deviation*100:.0f}% {direction} da nominal {nominal:.1f}A)",
            "Verificar carga mecânica, isolamento do enrolamento e alimentação elétrica"
        )
    elif deviation >= CURRENT_ALERT_PCT:
        direction = "acima" if current > nominal else "abaixo"
        return (
            "alert",
            f"Corrente fora do limite: {current:.2f}A ({deviation*100:.0f}% {direction} da nominal {nominal:.1f}A)",
            "Monitorar carga do motor e inspecionar conexões elétricas"
        )
    return ("normal", None, None)


def analyze(temperature: float, vibration: float, current: float,
            voltage: float, nominal_current: float) -> SensorStatus:
    """
    Analisa as leituras e retorna SensorStatus com classificação e
    decisão sobre geração de OS preditiva.
    """
    status = SensorStatus(
        temperature=temperature,
        vibration=vibration,
        current=current,
        voltage=voltage,
        nominal_current=nominal_current,
    )

    # Avaliar cada sensor
    t_status, t_anomaly, t_action = evaluate_temperature(temperature)
    v_status, v_anomaly, v_action = evaluate_vibration(vibration)
    c_status, c_anomaly, c_action = evaluate_current(current, nominal_current)

    status.temp_status    = t_status
    status.vib_status     = v_status
    status.current_status = c_status

    # Coletar anomalias
    for anomaly, action in [(t_anomaly, t_action), (v_anomaly, v_action), (c_anomaly, c_action)]:
        if anomaly:
            status.anomalies.append(anomaly)
            status.suggested_actions.append(action)

    # Regra de geração de OS:
    # - 1 sensor crítico → OS imediata
    # - 2+ sensores em alerta → OS preventiva
    critical_count = sum(1 for s in [t_status, v_status, c_status] if s == "critical")
    alert_count    = sum(1 for s in [t_status, v_status, c_status] if s == "alert")

    if critical_count >= 1:
        status.should_generate_os = True
        status.priority = "critica"
    elif alert_count >= 2:
        status.should_generate_os = True
        status.priority = "alta"

    return status


def status_to_dict(s: SensorStatus) -> dict:
    return {
        "temperature": s.temperature,
        "vibration": s.vibration,
        "current": s.current,
        "voltage": s.voltage,
        "temp_status": s.temp_status,
        "vib_status": s.vib_status,
        "current_status": s.current_status,
        "anomalies": s.anomalies,
        "suggested_actions": s.suggested_actions,
        "should_generate_os": s.should_generate_os,
        "priority": s.priority,
        "overall_status": (
            "critical" if any(x == "critical" for x in [s.temp_status, s.vib_status, s.current_status])
            else "alert" if any(x == "alert" for x in [s.temp_status, s.vib_status, s.current_status])
            else "normal"
        )
    }
