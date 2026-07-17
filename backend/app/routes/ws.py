import json
import logging
import asyncio
from typing import Set, Dict

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings

logger = logging.getLogger("gotot.ws")
settings = get_settings()


class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, Set[WebSocket]] = {}
        self._pubsub_connections: Dict[str, asyncio.Task] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active:
            self.active[task_id] = set()
        self.active[task_id].add(websocket)

        if task_id not in self._pubsub_connections:
            task = asyncio.create_task(self._listen_redis(task_id))
            self._pubsub_connections[task_id] = task

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

    async def _listen_redis(self, task_id: str):
        try:
            r = aioredis.from_url(
                settings.redis_url,
                socket_connect_timeout=2,
                decode_responses=True,
            )
            pubsub = r.pubsub()
            await pubsub.subscribe(f"progress:{task_id}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self.send_progress(task_id, data)
                    except (json.JSONDecodeError, Exception):
                        pass

                if task_id not in self.active:
                    break

            await pubsub.unsubscribe()
            await r.close()
        except Exception as e:
            logger.debug(f"Redis pubsub unavailable for {task_id}: {e}")


router = APIRouter(tags=["websocket"])

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
