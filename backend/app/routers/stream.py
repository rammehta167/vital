import asyncio
import json
from typing import Set
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1/stream", tags=["Real-time Stream"])

# Connected SSE listener queues
_subscribers: Set[asyncio.Queue] = set()


async def broadcast_event(event_type: str, data: dict):
    """Broadcast an SSE event payload to all active browser connections."""
    message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    for queue in list(_subscribers):
        try:
            queue.put_nowait(message)
        except Exception:
            _subscribers.discard(queue)


@router.get("")
async def stream_events():
    queue = asyncio.Queue()
    _subscribers.add(queue)

    async def event_generator():
        # Send initial ping
        yield f"event: ping\ndata: {json.dumps({'status': 'connected'})}\n\n"
        try:
            while True:
                # Wait for next event or send keep-alive every 15s
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield data
                except asyncio.TimeoutError:
                    yield "event: keepalive\ndata: {}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _subscribers.discard(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
