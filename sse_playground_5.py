import json
import uuid
from asyncio import sleep
from collections import deque

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = deque(maxlen=1000)


async def generate_dummy_model_response(prompt: str):
    # Simulate a model response with a delay
    await sleep(1)
    return f"Model response to: {prompt}"


@app.get("/push-event")
async def push_event(request: Request, prompt: str) -> dict:

    print(request)
    model_response = await generate_dummy_model_response(prompt)
    event = json.dumps(
        {
            "event": "message",
            "prompt": f"{prompt}",
            "model_response": f"{model_response}",
            "id": str(uuid.uuid4()),
        }
    )
    db.append(event)
    return {"status": "ok", "event": event}


@app.get("/my-stream")
async def stream(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            if len(db) > 0:
                yield db.pop()
                await sleep(1)

    return EventSourceResponse(event_generator(), media_type="text/event-stream")


@app.get("/chat")
async def chat_stream(request: Request, prompt: str):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            yield json.dumps(
                {
                    "event": "message",
                    "data": f"{prompt}",
                    "id": str(uuid.uuid4()),
                }
            )
            await sleep(1)

    return EventSourceResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5005)
