"""Gerenciador WebSocket — broadcast de leituras e alertas em tempo real."""
import asyncio
import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active:
                self.active.remove(websocket)

    async def broadcast(self, event: str, data: dict[str, Any]):
        payload = json.dumps({"event": event, "data": data, "ts": data.get("timestamp")})
        dead: list[WebSocket] = []
        async with self._lock:
            clients = list(self.active)
        for ws in clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)


ws_manager = ConnectionManager()
