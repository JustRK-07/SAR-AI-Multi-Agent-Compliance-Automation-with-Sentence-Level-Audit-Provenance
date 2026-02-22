from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio
import json

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time SAR generation progress."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        self.active_connections.pop(task_id, None)

    async def send_progress(self, task_id: str, data: dict):
        if websocket := self.active_connections.get(task_id):
            try:
                await websocket.send_json(data)
            except Exception:
                self.disconnect(task_id)

    async def broadcast(self, message: dict):
        for task_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(task_id)


manager = ConnectionManager()


@router.websocket("/ws/sar/{task_id}")
async def websocket_sar_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time SAR generation progress.

    Clients connect to this endpoint with the task_id received from POST /api/sar/generate.
    Progress updates are sent as JSON:
    {
        "stage": "data_analyst",  # Current agent
        "status": "processing",   # processing, complete, error
        "progress": 20,           # 0-100
        "message": "Extracting transaction facts..."
    }
    """
    await manager.connect(task_id, websocket)

    try:
        # Import here to avoid circular imports
        from app.routers.sar import generation_tasks

        # Send initial status
        if task_id in generation_tasks:
            await websocket.send_json(generation_tasks[task_id])

        # Keep connection alive and send updates
        while True:
            try:
                # Wait for any message from client (ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)

                # If client sends "status", respond with current status
                if data == "status" and task_id in generation_tasks:
                    await websocket.send_json(generation_tasks[task_id])

            except asyncio.TimeoutError:
                # No message received, check if task completed
                if task_id in generation_tasks:
                    task = generation_tasks[task_id]
                    await websocket.send_json(task)

                    # If task is done, close connection
                    if task.get("status") in ["completed", "failed"]:
                        await websocket.send_json({
                            "type": "complete",
                            "status": task.get("status"),
                            "sar_id": task.get("sar_id"),
                        })
                        break
                continue

    except WebSocketDisconnect:
        manager.disconnect(task_id)
    except Exception as e:
        manager.disconnect(task_id)
        print(f"WebSocket error for task {task_id}: {e}")


# Helper function to send progress updates from SAR generator
async def send_generation_progress(
    task_id: str,
    stage: str,
    status: str,
    progress: int,
    message: str,
):
    """
    Send progress update to connected WebSocket client.
    Called from SARGeneratorService during generation.
    """
    await manager.send_progress(
        task_id,
        {
            "stage": stage,
            "status": status,
            "progress": progress,
            "message": message,
        },
    )
