"""
Fonte de dados: placa ESP32 vs simulador (exclusão mútua).
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from database import SensorReading

DATA_LIVE_SECONDS = 12


def normalize_source(raw: Optional[str]) -> str:
    if raw is None or str(raw).strip() == "":
        return "esp32"
    s = str(raw).lower().strip()
    if s in ("esp32", "esp-32", "placa", "hardware"):
        return "esp32"
    if s in ("simulator", "simulador", "sim", "mock"):
        return "simulator"
    return "esp32"


def reading_is_live(last: Optional[SensorReading]) -> bool:
    if not last or not last.timestamp:
        return False
    age = datetime.utcnow() - last.timestamp
    return age <= timedelta(seconds=DATA_LIVE_SECONDS)


def esp32_sending_live(db: Session) -> bool:
    last = (
        db.query(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )
    if not last:
        return False
    return normalize_source(last.source) == "esp32" and reading_is_live(last)


def validate_sensor_values(
    temperature: float,
    vibration: float,
    current: float,
    voltage: float,
    source: str,
) -> None:
    """Levanta ValueError com mensagem em português se valores inválidos."""
    if temperature < -40 or temperature > 200:
        raise ValueError(
            f"Temperatura inválida ({temperature}°C). Verifique o sensor na placa."
        )
    if vibration < 0 or vibration > 500:
        raise ValueError(f"Vibração inválida ({vibration} mm/s).")
    if current < 0 or current > 500:
        raise ValueError(f"Corrente inválida ({current} A).")
    if voltage < 0 or voltage > 1000:
        raise ValueError(f"Tensão inválida ({voltage} V).")

    if source == "esp32" and temperature < 0:
        raise ValueError(
            "Leitura de temperatura falhou no ESP32 (valor negativo). "
            "Confira o sensor DHT22/LM35 e os pinos."
        )
