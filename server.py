"""Same-origin website and restricted LiveKit token endpoint. Run one worker."""
import json
import os
import time
from collections import defaultdict, deque
from datetime import timedelta
from pathlib import Path
from typing import Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from livekit import api
from pydantic import BaseModel, Field
from chat_api import router as chat_router
from enquiry_api import router as enquiry_router
from voice_config import AGENT_NAME, LANGUAGES, SESSION_SECONDS

load_dotenv()
app = FastAPI(docs_url=None, redoc_url=None)
app.include_router(chat_router)
app.include_router(enquiry_router)
ROOT = Path(__file__).resolve().parent
attempts = defaultdict(deque)


class CallRequest(BaseModel):
    name: str = Field(default="", max_length=80)
    company: str = Field(default="", max_length=120)
    goal: Literal["automation", "sales", "service"] = "automation"
    language: str = "te-IN"


@app.post("/api/voice/token")
async def voice_token(body: CallRequest, request: Request):
    if request.headers.get("origin") != os.getenv("VOICE_ALLOWED_ORIGIN", "http://localhost:8000"):
        raise HTTPException(403, "This website origin is not allowed.")
    if body.language not in LANGUAGES:
        raise HTTPException(422, "Choose a supported language.")
    if not all(os.getenv(k) for k in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "SARVAM_API_KEY")):
        raise HTTPException(503, "Voice calling is not configured yet. Please try again later.")
    now = time.monotonic()
    for key in list(attempts):
        if not attempts[key] or attempts[key][-1] <= now - 600:
            del attempts[key]
    recent = attempts[request.client.host if request.client else "unknown"]
    while recent and recent[0] <= now - 600:
        recent.popleft()
    if len(recent) >= 3:
        raise HTTPException(429, "Call limit reached. Please try again in ten minutes.")
    recent.append(now)
    room = f"voice-{uuid4().hex}"
    metadata = json.dumps(body.model_dump(), ensure_ascii=False)
    token = (api.AccessToken()
        .with_identity(f"visitor-{uuid4().hex}")
        .with_name(body.name or "Visitor")
        .with_ttl(timedelta(seconds=60))
        .with_grants(api.VideoGrants(room_join=True, room=room,
            can_publish=True, can_publish_sources=["microphone"],
            can_subscribe=True, can_publish_data=False))
        .with_room_config(api.RoomConfiguration(
            max_participants=2, empty_timeout=30,
            agents=[api.RoomAgentDispatch(agent_name=AGENT_NAME, metadata=metadata)]))
        .to_jwt())
    return JSONResponse({"server_url": os.environ["LIVEKIT_URL"],
        "participant_token": token, "duration_seconds": SESSION_SECONDS},
        headers={"Cache-Control": "no-store"})


# Browsers must revalidate (a cheap 304 via ETag) so an edit never pairs new HTML with stale CSS.
NO_CACHE = {"Cache-Control": "no-cache"}


# Explicit allowlist: never expose .env, Python source, or the project directory.
@app.get("/")
async def index():
    return FileResponse(ROOT / "index.html", headers=NO_CACHE)


@app.get("/{asset}")
async def asset(asset: str):
    if asset not in {"index.html", "app.js", "voice.js", "styles.css", "logo-openai.svg", "logo-nvidia.svg", "logo-sarvam.png", "logo-claude.svg"}:
        raise HTTPException(404)
    return FileResponse(ROOT / asset, headers=NO_CACHE)
