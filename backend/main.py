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
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal, init_db, SensorReading, ServiceOrder, MotorState, get_db
from predictive import analyze, status_to_dict

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


class MotorConfig(BaseModel):
    nominal_current: Optional[float] = None


class SimulatorStartIn(BaseModel):
    profile: str = "normal"
    cycle: bool = False


# ─── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()


# ─── Geração de OS em background ─────────────────────────────────────────────

def generate_os_background(reading_id: int, status_data: dict, db_session_factory):
    """Gera OS preditiva e PDF em background."""
    try:
        from service_order_gen import generate_pdf  # importação lazy
    except ImportError:
        generate_pdf = None

    db = db_session_factory()
    try:
        reading = db.query(SensorReading).filter(SensorReading.id == reading_id).first()
        if not reading:
            return

        # Verificar se já existe OS recente (últimos 5 min) para evitar duplicatas
        from datetime import timedelta
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_os = db.query(ServiceOrder).filter(ServiceOrder.created_at >= five_min_ago).first()
        if recent_os:
            return  # Já gerou OS recentemente

        # Número sequencial
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

        # Gerar PDF se disponível
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
    """Recebe leitura dos sensores (ESP32 real ou simulador)."""
    # Buscar corrente nominal configurada
    motor = db.query(MotorState).first()
    nominal_current = motor.nominal_current if motor else 8.0

    # Análise preditiva
    analysis = analyze(data.temperature, data.vibration, data.current, data.voltage, nominal_current)

    # Salvar leitura
    reading = SensorReading(
        temperature=data.temperature,
        vibration=data.vibration,
        current=data.current,
        voltage=data.voltage,
        rpm=data.rpm,
        source=data.source,
        temp_status=analysis.temp_status,
        vibration_status=analysis.vib_status,
        current_status=analysis.current_status,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Atualizar estado de running se há leitura com corrente
    if motor and data.current > 0.5:
        motor.is_running = True
        motor.updated_at = datetime.utcnow()
        db.commit()

    # Gerar OS em background se necessário
    status_data = status_to_dict(analysis)
    if analysis.should_generate_os:
        background_tasks.add_task(
            generate_os_background, reading.id, status_data, SessionLocal
        )

    return {
        "id": reading.id,
        "timestamp": reading.timestamp.isoformat(),
        "analysis": status_data,
    }


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
        for r in reversed(rows)  # cronológico para gráficos
    ]


# Leitura considerada "ao vivo" se chegou nos últimos N segundos (simulador ~2s)
DATA_LIVE_SECONDS = 12


def _reading_is_live(last: SensorReading | None) -> bool:
    if not last or not last.timestamp:
        return False
    age = datetime.utcnow() - last.timestamp
    return age <= timedelta(seconds=DATA_LIVE_SECONDS)


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
    download_name = f"Ordem de Servico {order.os_number}.pdf"
    return FileResponse(
        order.pdf_path,
        media_type="application/pdf",
        filename=download_name,
    )


@app.post("/api/motor/start")
def motor_start(db: Session = Depends(get_db)):
    """Registra que o motor foi ligado."""
    motor = db.query(MotorState).first()
    if motor:
        motor.is_running = True
        motor.updated_at = datetime.utcnow()
        db.commit()
    return {"status": "running"}


@app.post("/api/motor/stop")
def motor_stop(db: Session = Depends(get_db)):
    """Registra que o motor foi desligado."""
    motor = db.query(MotorState).first()
    if motor:
        motor.is_running = False
        motor.updated_at = datetime.utcnow()
        db.commit()
    return {"status": "stopped"}


@app.put("/api/motor/config")
def motor_config(config: MotorConfig, db: Session = Depends(get_db)):
    """Atualiza configuração do motor (corrente nominal)."""
    motor = db.query(MotorState).first()
    if motor and config.nominal_current is not None:
        motor.nominal_current = config.nominal_current
        db.commit()
    return {"nominal_current": motor.nominal_current if motor else 8.0}


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# ─── Simulador de sensores ───────────────────────────────────────────────────

@app.get("/api/simulator/status")
def simulator_status():
    """Retorna se o simulador está rodando e com qual perfil."""
    from simulator_control import get_status, PROFILE_LABELS, VALID_PROFILES
    return {
        **get_status(),
        "profiles": [
            {"id": p, "label": PROFILE_LABELS[p]} for p in VALID_PROFILES
        ],
    }


@app.post("/api/simulator/start")
def simulator_start(body: SimulatorStartIn):
    """Inicia o simulador de sensores (substitui ESP32 em demonstração)."""
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
    """Encerra o simulador de sensores."""
    from simulator_control import stop_simulator
    return stop_simulator()


# ─── Thresholds configuráveis via API ────────────────────────────────────────
from pydantic import BaseModel as _BM
from typing import Optional as _Opt

class ThresholdConfig(_BM):
    temp_alert:            _Opt[float] = None
    temp_critical:         _Opt[float] = None
    vib_alert:             _Opt[float] = None
    vib_critical:          _Opt[float] = None
    current_alert_pct:     _Opt[float] = None
    current_critical_pct:  _Opt[float] = None

@app.put("/api/thresholds")
def set_thresholds(cfg: ThresholdConfig):
    """Atualiza limites de alarme em runtime (sem reiniciar)."""
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
    """Retorna limites atuais."""
    import predictive as _p
    return {
        "temp_alert": _p.TEMP_ALERT, "temp_critical": _p.TEMP_CRITICAL,
        "vib_alert": _p.VIB_ALERT, "vib_critical": _p.VIB_CRITICAL,
        "current_alert_pct": _p.CURRENT_ALERT_PCT * 100,
        "current_critical_pct": _p.CURRENT_CRITICAL_PCT * 100,
    }
