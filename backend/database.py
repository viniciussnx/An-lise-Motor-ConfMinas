from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./motor_monitor.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    temperature = Column(Float, nullable=False)       # °C
    vibration = Column(Float, nullable=False)         # mm/s
    current = Column(Float, nullable=False)           # A
    voltage = Column(Float, nullable=False)           # V
    rpm = Column(Float, nullable=True)                # RPM (opcional)
    source = Column(String(20), default="esp32")      # "esp32" ou "simulator"

    # Status calculado
    temp_status = Column(String(10), default="normal")       # normal/alert/critical
    vibration_status = Column(String(10), default="normal")
    current_status = Column(String(10), default="normal")


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id = Column(Integer, primary_key=True, index=True)
    os_number = Column(String(20), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    equipment = Column(String(100), default="Motor Trifásico WEG W22")
    location = Column(String(100), default="Sala de Máquinas - Setor A")

    # Leituras no momento da detecção
    temperature = Column(Float)
    vibration = Column(Float)
    current = Column(Float)
    voltage = Column(Float)

    # Anomalias e análise
    anomalies = Column(Text)        # JSON com lista de anomalias
    priority = Column(String(10))   # "alta" ou "critica"
    actions = Column(Text)          # JSON com ações sugeridas
    status = Column(String(20), default="aberta")   # aberta | fechada
    closed_at = Column(DateTime, nullable=True)
    pdf_path = Column(String(200), nullable=True)


class MotorState(Base):
    __tablename__ = "motor_state"

    id = Column(Integer, primary_key=True, index=True)
    is_running = Column(Boolean, default=False)
    nominal_current = Column(Float, default=8.0)    # A — corrente nominal configurada
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    # Migração leve: coluna closed_at em bancos existentes
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE service_orders ADD COLUMN closed_at DATETIME"))
            conn.commit()
    except Exception:
        pass
    # Inicializa estado do motor se não existir
    db = SessionLocal()
    try:
        if db.query(MotorState).count() == 0:
            db.add(MotorState(is_running=False, nominal_current=8.0))
            db.commit()
    finally:
        db.close()
