# import asyncio

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from openai import AsyncOpenAI
from sse_starlette.sse import EventSourceResponse

load_dotenv(override=True)


app = FastAPI()
client = AsyncOpenAI()


async def generate_response(prompt: str):
    # prompt = "I'm a plumber, I can fix a toilet"
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a helpful assistant of job matching platform.
                                             You are helping new users to fill the page about themselves.
                                             Ask them a question to better describe them.
                                             You speak only Russian.""",
            },
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )

    # ai_comp = completion.choices[0].message.dict()
    async for chunk in response:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content


@app.get("/chat")
async def chat(request: Request, prompt: str):
    async def event_generator():
        async for content in generate_response(prompt):
            if await request.is_disconnected():
                break
            yield {"data": content}

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    uvicorn.run("sse_playground:app", host="0.0.0.0", port=5002, log_level="info")
