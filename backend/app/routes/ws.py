import json
import logging
import asyncio
from typing import Set, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("gotot.ws")

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, Set[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active:
            self.active[task_id] = set()
        self.active[task_id].add(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket):
        if task_id in self.active:
            self.active[task_id].discard(websocket)
            if not self.active[task_id]:
                del self.active[task_id]

    async def send_progress(self, task_id: str, data: dict):
        if task_id in self.active:
            dead = set()
            for ws in self.active[task_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                self.active[task_id].discard(ws)
            if not self.active[task_id]:
                del self.active[task_id]


manager = ConnectionManager()


@router.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    await manager.connect(task_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)
    except Exception:
        manager.disconnect(task_id, websocket)
