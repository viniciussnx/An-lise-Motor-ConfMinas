"""
DEMANDA CONFIMINAS - Sistema de Manutenção Preditiva
Backend FastAPI — porta 8000

Endpoints:
  POST /api/readings          — recebe dados dos sensores (ESP32 ou simulador)
  GET  /api/readings          — histórico de leituras
  GET  /api/status            — status atual do motor
  GET  /api/service-orders    — lista de ordens de serviço
  POST /api/motor/start       — ligar motor (via ESP32)
  POST /api/motor/stop        — desligar motor (via ESP32)
  GET  /api/predictive        — análise preditiva da última leitura
  GET  /api/service-orders/{id}/pdf — download do PDF da OS
  PATCH /api/service-orders/{id}/fechar — confirma e fecha a OS
  GET  /api/simulator/status   — status do simulador
  POST /api/simulator/start    — inicia simulador
  POST /api/simulator/stop     — para simulador
  POST /api/sensors            — recebe dados do simulador web (formato nested)
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from database import SessionLocal, init_db, SensorReading, ServiceOrder, MotorState, get_db
from predictive import analyze, status_to_dict
from data_source import (
    normalize_source,
    reading_is_live,
    esp32_sending_live,
)
from readings_service import ingest_reading, nested_payload_to_flat

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Motor Monitor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas de entrada ───────────────────────────────────────────────────────

class ReadingIn(BaseModel):
    temperature: float          # °C
    vibration: float            # mm/s
    current: float              # A
    voltage: float              # V
    rpm: Optional[float] = None
    source: Optional[str] = "esp32"

    @field_validator("source", mode="before")
    @classmethod
    def _norm_source(cls, v):
        return normalize_source(v)


class MotorConfig(BaseModel):
    nominal_current: Optional[float] = None


class SimulatorStartIn(BaseModel):
    profile: str = "normal"
    cycle: bool = False


# ─── Schemas do simulador web (formato nested) ────────────────────────────────

class WebVibration(BaseModel):
    detected: bool
    amplitude: float
    frequency: float


class WebTemperature(BaseModel):
    celsius: float
    humidity: float


class WebElectrical(BaseModel):
    voltage: float
    current: float
    power: float


class WebMotor(BaseModel):
    speed: int
    rpm: int


class SimulatorPayload(BaseModel):
    device_id: str
    timestamp: int
    vibration: WebVibration
    temperature: WebTemperature
    electrical: WebElectrical
    motor: WebMotor


# ─── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()


# ─── Geração de OS em background ─────────────────────────────────────────────

def generate_os_background(reading_id: int, status_data: dict, db_session_factory):
    """Gera OS preditiva e PDF em background."""
    try:
        from service_order_gen import generate_pdf
    except ImportError:
        generate_pdf = None

    db = db_session_factory()
    try:
        reading = db.query(SensorReading).filter(SensorReading.id == reading_id).first()
        if not reading:
            return

        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_os = db.query(ServiceOrder).filter(ServiceOrder.created_at >= five_min_ago).first()
        if recent_os:
            return

        count = db.query(ServiceOrder).count() + 1
        os_number = f"OS-{datetime.utcnow().strftime('%Y%m%d')}-{count:04d}"

        os_obj = ServiceOrder(
            os_number=os_number,
            equipment="Motor Trifásico WEG W22",
            location="Sala de Máquinas - Setor A",
            temperature=reading.temperature,
            vibration=reading.vibration,
            current=reading.current,
            voltage=reading.voltage,
            anomalies=json.dumps(status_data["anomalies"], ensure_ascii=False),
            priority=status_data["priority"],
            actions=json.dumps(status_data["suggested_actions"], ensure_ascii=False),
            status="aberta",
        )
        db.add(os_obj)
        db.commit()
        db.refresh(os_obj)

        if generate_pdf:
            pdf_path = generate_pdf(os_obj)
            if pdf_path:
                os_obj.pdf_path = pdf_path
                db.commit()

        print(f"[OS] Gerada: {os_number} | Prioridade: {status_data['priority']}")
    except Exception as e:
        print(f"[OS] Erro ao gerar OS: {e}")
    finally:
        db.close()


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/api/readings", status_code=201)
def post_reading(
    data: ReadingIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Recebe leitura dos sensores (ESP32 real ou simulador Python)."""
    try:
        result = ingest_reading(
            db,
            temperature=data.temperature,
            vibration=data.vibration,
            current=data.current,
            voltage=data.voltage,
            source=data.source or "esp32",
            rpm=data.rpm,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    reading = result["reading"]
    status_data = result["status_data"]
    if result["should_generate_os"]:
        background_tasks.add_task(
            generate_os_background, reading.id, status_data, SessionLocal
        )

    return {
        "id": reading.id,
        "timestamp": reading.timestamp.isoformat(),
        "analysis": status_data,
    }


# ─── Simulador Web (formato nested) ──────────────────────────────────────────

@app.post("/api/sensors", status_code=201)
def receive_web_simulator(
    data: SimulatorPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Recebe dados do simulador web (HTML) — grava no banco, alimenta gráficos e gera OS."""
    flat = nested_payload_to_flat(data)
    try:
        result = ingest_reading(
            db,
            temperature=flat["temperature"],
            vibration=flat["vibration"],
            current=flat["current"],
            voltage=flat["voltage"],
            source="simulator",
            rpm=flat["rpm"],
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    reading = result["reading"]
    status_data = result["status_data"]
    if result["should_generate_os"]:
        background_tasks.add_task(
            generate_os_background, reading.id, status_data, SessionLocal
        )

    print(
        f"[WEB-SIM] {data.device_id} | T:{flat['temperature']:.1f}°C "
        f"V:{flat['vibration']:.2f}mm/s I:{flat['current']:.2f}A"
    )

    return {
        "status": "ok",
        "device_id": data.device_id,
        "reading_id": reading.id,
        "timestamp": reading.timestamp.isoformat(),
        "analysis": status_data,
        "data_live": True,
    }


# ─── Histórico ────────────────────────────────────────────────────────────────

@app.get("/api/readings")
def get_readings(limit: int = 60, db: Session = Depends(get_db)):
    """Retorna histórico de leituras para o dashboard."""
    rows = (
        db.query(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "temperature": r.temperature,
            "vibration": r.vibration,
            "current": r.current,
            "voltage": r.voltage,
            "rpm": r.rpm,
            "source": r.source,
            "temp_status": r.temp_status,
            "vibration_status": r.vibration_status,
            "current_status": r.current_status,
        }
        for r in reversed(rows)
    ]


def _reading_is_live(last: SensorReading | None) -> bool:
    return reading_is_live(last)


@app.get("/api/status")
def get_status(db: Session = Depends(get_db)):
    """Status atual do motor e última análise preditiva."""
    motor = db.query(MotorState).first()
    last = (
        db.query(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )

    nominal = motor.nominal_current if motor else 8.0
    data_live = _reading_is_live(last)

    if not last or not data_live:
        return {
            "is_running": False,
            "nominal_current": nominal,
            "last_reading": None,
            "overall_status": "no_data",
            "data_live": False,
            "temp_status": "no_data",
            "vib_status": "no_data",
            "current_status": "no_data",
            "anomalies": [],
        }

    analysis = analyze(last.temperature, last.vibration, last.current, last.voltage, nominal)
    status_data = status_to_dict(analysis)

    return {
        "is_running": bool(motor.is_running) if motor else False,
        "nominal_current": nominal,
        "data_live": True,
        "last_reading": {
            "timestamp": last.timestamp.isoformat(),
            "temperature": last.temperature,
            "vibration": last.vibration,
            "current": last.current,
            "voltage": last.voltage,
            "source": last.source,
        },
        **status_data,
    }


@app.get("/api/predictive")
def get_predictive(db: Session = Depends(get_db)):
    """Análise preditiva detalhada da última leitura."""
    return get_status(db=db)


@app.get("/api/service-orders")
def get_service_orders(db: Session = Depends(get_db)):
    """Lista todas as ordens de serviço."""
    orders = db.query(ServiceOrder).order_by(ServiceOrder.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "os_number": o.os_number,
            "created_at": o.created_at.isoformat(),
            "equipment": o.equipment,
            "location": o.location,
            "temperature": o.temperature,
            "vibration": o.vibration,
            "current": o.current,
            "voltage": o.voltage,
            "anomalies": json.loads(o.anomalies) if o.anomalies else [],
            "priority": o.priority,
            "actions": json.loads(o.actions) if o.actions else [],
            "status": o.status,
            "closed_at": o.closed_at.isoformat() if o.closed_at else None,
            "has_pdf": bool(o.pdf_path and os.path.exists(o.pdf_path)),
        }
        for o in orders
    ]


@app.patch("/api/service-orders/{os_id}/fechar")
def close_service_order(os_id: int, db: Session = Depends(get_db)):
    """Confirma e move a OS para o status fechada."""
    order = db.query(ServiceOrder).filter(ServiceOrder.id == os_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    if order.status == "fechada":
        return {"ok": True, "os_number": order.os_number, "status": "fechada", "message": "OS já estava fechada"}
    order.status = "fechada"
    order.closed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "os_number": order.os_number, "status": "fechada"}


@app.get("/api/service-orders/{os_id}/pdf")
def download_os_pdf(os_id: int, db: Session = Depends(get_db)):
    """Download do PDF de uma OS."""
    order = db.query(ServiceOrder).filter(ServiceOrder.id == os_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    if not order.pdf_path or not os.path.exists(order.pdf_path):
        raise HTTPException(status_code=404, detail="PDF não disponível")
    return FileResponse(
        order.pdf_path,
        media_type="application/pdf",
        filename=f"Ordem de Servico {order.os_number}.pdf",
    )


@app.post("/api/motor/start")
def motor_start(db: Session = Depends(get_db)):
    motor = db.query(MotorState).first()
    if motor:
        motor.is_running = True
        motor.updated_at = datetime.utcnow()
        db.commit()
    return {"status": "running"}


@app.post("/api/motor/stop")
def motor_stop(db: Session = Depends(get_db)):
    motor = db.query(MotorState).first()
    if motor:
        motor.is_running = False
        motor.updated_at = datetime.utcnow()
        db.commit()
    return {"status": "stopped"}


@app.put("/api/motor/config")
def motor_config(config: MotorConfig, db: Session = Depends(get_db)):
    motor = db.query(MotorState).first()
    if motor and config.nominal_current is not None:
        motor.nominal_current = config.nominal_current
        db.commit()
    return {"nominal_current": motor.nominal_current if motor else 8.0}


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# ─── Simulador de sensores (interno) ─────────────────────────────────────────

@app.get("/api/simulator/status")
def simulator_status(db: Session = Depends(get_db)):
    from simulator_control import get_status, PROFILE_LABELS, VALID_PROFILES
    last = (
        db.query(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )
    return {
        **get_status(),
        "esp32_active": esp32_sending_live(db),
        "last_source": normalize_source(last.source) if last else None,
        "profiles": [
            {"id": p, "label": PROFILE_LABELS[p]} for p in VALID_PROFILES
        ],
    }


@app.post("/api/simulator/start")
def simulator_start(body: SimulatorStartIn):
    from simulator_control import start_simulator
    try:
        return start_simulator(profile=body.profile, cycle=body.cycle)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/api/simulator/stop")
def simulator_stop():
    from simulator_control import stop_simulator
    return stop_simulator()


@app.post("/api/simulator/prepare-esp32")
def prepare_esp32_mode():
    from simulator_control import stop_simulator
    return {
        **stop_simulator(),
        "mode": "esp32",
        "message": "Simulador parado. Pode usar a placa ESP32.",
    }


# ─── Thresholds configuráveis via API ─────────────────────────────────────────

class ThresholdConfig(BaseModel):
    temp_alert:            Optional[float] = None
    temp_critical:         Optional[float] = None
    vib_alert:             Optional[float] = None
    vib_critical:          Optional[float] = None
    current_alert_pct:     Optional[float] = None
    current_critical_pct:  Optional[float] = None


@app.put("/api/thresholds")
def set_thresholds(cfg: ThresholdConfig):
    import predictive as _p
    if cfg.temp_alert           is not None: _p.TEMP_ALERT            = cfg.temp_alert
    if cfg.temp_critical        is not None: _p.TEMP_CRITICAL         = cfg.temp_critical
    if cfg.vib_alert            is not None: _p.VIB_ALERT             = cfg.vib_alert
    if cfg.vib_critical         is not None: _p.VIB_CRITICAL          = cfg.vib_critical
    if cfg.current_alert_pct    is not None: _p.CURRENT_ALERT_PCT     = cfg.current_alert_pct / 100
    if cfg.current_critical_pct is not None: _p.CURRENT_CRITICAL_PCT  = cfg.current_critical_pct / 100
    return {
        "temp_alert": _p.TEMP_ALERT, "temp_critical": _p.TEMP_CRITICAL,
        "vib_alert": _p.VIB_ALERT, "vib_critical": _p.VIB_CRITICAL,
        "current_alert_pct": _p.CURRENT_ALERT_PCT * 100,
        "current_critical_pct": _p.CURRENT_CRITICAL_PCT * 100,
    }


@app.get("/api/thresholds")
def get_thresholds():
    import predictive as _p
    return {
        "temp_alert": _p.TEMP_ALERT, "temp_critical": _p.TEMP_CRITICAL,
        "vib_alert": _p.VIB_ALERT, "vib_critical": _p.VIB_CRITICAL,
        "current_alert_pct": _p.CURRENT_ALERT_PCT * 100,
        "current_critical_pct": _p.CURRENT_CRITICAL_PCT * 100,
    }


# ─── Simulador web (HTML estático) ────────────────────────────────────────────

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/simulator")
def serve_simulator():
    """Abre o simulador web em http://localhost:8000/simulator"""
    html = STATIC_DIR / "esp32_simulator.html"
    if not html.is_file():
        raise HTTPException(status_code=404, detail="Simulador web não encontrado em backend/static/")
    return FileResponse(str(html))