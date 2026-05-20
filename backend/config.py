"""Configuração central — variáveis de ambiente com defaults para Mac local."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'motor_monitor.db'}")

MQTT_ENABLED = os.getenv("MQTT_ENABLED", "true").lower() == "true"
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")
MQTT_TOPIC_TELEMETRY = os.getenv("MQTT_TOPIC_TELEMETRY", "confiminas/motor/+/telemetry")
MQTT_TOPIC_STATUS = os.getenv("MQTT_TOPIC_STATUS", "confiminas/motor/+/status")

DEVICE_OFFLINE_SEC = int(os.getenv("DEVICE_OFFLINE_SEC", "15"))
API_KEY = os.getenv("API_KEY", "")  # vazio = sem auth (dev local)

DEFAULT_MOTOR_NAME = os.getenv("MOTOR_NAME", "Motor Trifásico WEG W22")
DEFAULT_MOTOR_LOCATION = os.getenv("MOTOR_LOCATION", "Sala de Máquinas - Setor A")
