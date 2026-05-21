"""
Autenticação simples por token assinado (HMAC-SHA256).
- Credenciais padrão: Vinícius / master (overridable via env AUTH_USER / AUTH_PASS)
- Sem dependências externas (usa apenas hmac/hashlib/secrets/json).
"""
from __future__ import annotations

import base64
import hmac
import hashlib
import json
import os
import secrets
import time
from typing import Optional

from fastapi import Header, HTTPException, status

# ─── Config ──────────────────────────────────────────────────────────────────

AUTH_USER = os.getenv("AUTH_USER", "Vinícius")
AUTH_PASS = os.getenv("AUTH_PASS", "master")
AUTH_SECRET = os.getenv("AUTH_SECRET") or secrets.token_hex(32)
TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TTL", str(60 * 60 * 12)))   # 12h

# Quando AUTH_DISABLED=true a API não exige token (útil em dev).
AUTH_DISABLED = os.getenv("AUTH_DISABLED", "false").lower() == "true"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _sign(payload_b64: str) -> str:
    sig = hmac.new(AUTH_SECRET.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(sig)


# ─── API pública ─────────────────────────────────────────────────────────────

def verify_credentials(username: str, password: str) -> bool:
    u_ok = hmac.compare_digest(
        (username or "").encode("utf-8"),
        AUTH_USER.encode("utf-8"),
    )
    p_ok = hmac.compare_digest(
        (password or "").encode("utf-8"),
        AUTH_PASS.encode("utf-8"),
    )
    return u_ok and p_ok


def create_token(username: str) -> dict:
    issued = int(time.time())
    expires = issued + TOKEN_TTL_SECONDS
    payload = {"sub": username, "iat": issued, "exp": expires}
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig_b64 = _sign(payload_b64)
    return {
        "token": f"{payload_b64}.{sig_b64}",
        "expires_at": expires,
        "username": username,
    }


def decode_token(token: str) -> Optional[dict]:
    try:
        payload_b64, sig_b64 = token.split(".", 1)
    except ValueError:
        return None

    expected = _sign(payload_b64)
    if not hmac.compare_digest(expected, sig_b64):
        return None

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (ValueError, json.JSONDecodeError):
        return None

    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload


# ─── Dependência FastAPI ─────────────────────────────────────────────────────

def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """Use como Depends(require_auth) nos endpoints protegidos."""
    if AUTH_DISABLED:
        return {"sub": AUTH_USER, "anon": True}

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
