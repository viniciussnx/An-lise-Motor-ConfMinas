"""
Persistência e validação unificada de leituras (ESP32, simulador Python, simulador web).
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database import SensorReading, MotorState
from predictive import analyze, status_to_dict
from data_source import normalize_source, validate_sensor_values, esp32_sending_live


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def web_vibration_to_mm_s(amplitude: float, frequency: float, detected: bool) -> float:
    """
    Simulador web envia amplitude em g (0–1).
    O dashboard e a análise preditiva usam mm/s (alerta 25, crítico 35).
    """
    if amplitude <= 2.0:
        base = amplitude * 80.0
        if detected:
            base += frequency * 0.08
        return round(max(0.0, base), 2)
    return round(amplitude, 2)


def nested_payload_to_flat(data) -> dict:
    """Converte SimulatorPayload (nested) para campos planos do banco."""
    temp = data.temperature.celsius
    vib = web_vibration_to_mm_s(
        data.vibration.amplitude,
        data.vibration.frequency,
        data.vibration.detected,
    )
    current = data.electrical.current
    voltage = data.electrical.voltage
    rpm = float(data.motor.rpm)
    return {
        "temperature": temp,
        "vibration": vib,
        "current": current,
        "voltage": voltage,
        "rpm": rpm,
    }


def ingest_reading(
    db: Session,
    *,
    temperature: float,
    vibration: float,
    current: float,
    voltage: float,
    source: str,
    rpm: Optional[float] = None,
    stop_sim_on_esp32: bool = True,
    reject_sim_if_esp32: bool = True,
) -> dict:
    """
    Valida, grava leitura, atualiza motor e retorna análise.
    Levanta ValueError (422) ou RuntimeError/HTTPException via caller.
    """
    src = normalize_source(source)

    validate_sensor_values(temperature, vibration, current, voltage, src)

    if src == "simulator" and reject_sim_if_esp32 and esp32_sending_live(db):
        raise RuntimeError(
            "Placa ESP32 ativa. Pare o simulador ou use ./start.sh --real antes de enviar dados simulados."
        )

    if src == "esp32" and stop_sim_on_esp32:
        from simulator_control import stop_simulator
        stop_simulator()

    motor = db.query(MotorState).first()
    nominal = motor.nominal_current if motor else 8.0

    analysis = analyze(temperature, vibration, current, voltage, nominal)

    reading = SensorReading(
        temperature=temperature,
        vibration=vibration,
        current=current,
        voltage=voltage,
        rpm=rpm,
        source=src,
        temp_status=analysis.temp_status,
        vibration_status=analysis.vib_status,
        current_status=analysis.current_status,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    if motor and current > 0.5:
        motor.is_running = True
        motor.updated_at = _utcnow()
        db.commit()

    status_data = status_to_dict(analysis)
    return {
        "reading": reading,
        "analysis": analysis,
        "status_data": status_data,
        "should_generate_os": analysis.should_generate_os,
    }
