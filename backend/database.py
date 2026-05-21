"""
Camada de persistência — SQLAlchemy 2.x + SQLite.

Otimizações aplicadas:
- WAL mode (escrita concorrente sem bloquear leituras)
- Índice composto (source, timestamp) para queries de "última leitura por fonte"
- pragmas de performance (synchronous=NORMAL, cache_size, mmap)
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'motor_monitor.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_pragmas(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-8000")     # ~8 MiB
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=134217728")  # 128 MiB
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    temperature = Column(Float, nullable=False)
    vibration = Column(Float, nullable=False)
    current = Column(Float, nullable=False)
    voltage = Column(Float, nullable=False)
    rpm = Column(Float, nullable=True)
    source = Column(String(20), default="esp32", index=True)

    temp_status = Column(String(10), default="normal")
    vibration_status = Column(String(10), default="normal")
    current_status = Column(String(10), default="normal")

    __table_args__ = (
        Index("ix_sensor_readings_source_ts", "source", "timestamp"),
    )


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id = Column(Integer, primary_key=True, index=True)
    os_number = Column(String(20), unique=True, index=True)
    created_at = Column(DateTime, default=_utcnow, index=True)
    equipment = Column(String(100), default="Motor Trifásico WEG W22")
    location = Column(String(100), default="Sala de Máquinas - Setor A")

    temperature = Column(Float)
    vibration = Column(Float)
    current = Column(Float)
    voltage = Column(Float)

    anomalies = Column(Text)
    priority = Column(String(10))
    actions = Column(Text)
    status = Column(String(20), default="aberta", index=True)
    closed_at = Column(DateTime, nullable=True)
    pdf_path = Column(String(200), nullable=True)


class MotorState(Base):
    __tablename__ = "motor_state"

    id = Column(Integer, primary_key=True, index=True)
    is_running = Column(Boolean, default=False)
    nominal_current = Column(Float, default=8.0)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    # Migração leve: coluna closed_at em bancos antigos
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE service_orders ADD COLUMN closed_at DATETIME"))
            conn.commit()
        except Exception:
            conn.rollback()

    db = SessionLocal()
    try:
        motor = db.query(MotorState).first()
        if not motor:
            db.add(MotorState(is_running=False, nominal_current=2.0))
            db.commit()
        elif motor.nominal_current == 8.0:
            # Atualiza padrão antigo (motor industrial) para protótipo DC
            motor.nominal_current = 2.0
            db.commit()
    finally:
        db.close()
