"""Same-origin website and restricted LiveKit token endpoint. Run one worker."""
import json
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from livekit import api
from pydantic import BaseModel, Field
from chat_api import check_origin, router as chat_router
from enquiry_api import prepare_database, router as enquiry_router
from voice_config import AGENT_NAME, LANGUAGES, SESSION_SECONDS

load_dotenv()


@asynccontextmanager
async def lifespan(_app):
    # Create or upgrade the enquiry tables before traffic. Failures are logged, never fatal.
    await run_in_threadpool(prepare_database)
    yield


# No interactive docs or OpenAPI schema in production.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.include_router(chat_router)
app.include_router(enquiry_router)
ROOT = Path(__file__).resolve().parent
attempts = defaultdict(deque)
# Explicit allowlist: never expose .env, Python source, or the project directory.
PUBLIC_FILES = frozenset({"index.html", "app.js", "playground.js", "launchCampaign.js", "voice.js", "styles.css", "favicon.svg", "favicon.ico",
                          "logo-openai.svg", "logo-nvidia.svg", "logo-sarvam.png", "logo-claude.svg"})


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Permissions-Policy", "microphone=(self), camera=(), geolocation=()")
    # Behind Railway's TLS proxy the scheme is https once FORWARDED_ALLOW_IPS trusts the proxy.
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return response


class CallRequest(BaseModel):
    name: str = Field(default="", max_length=80)
    company: str = Field(default="", max_length=120)
    goal: Literal["automation", "sales", "service"] = "automation"
    language: str = "te-IN"


@app.post("/api/voice/token")
async def voice_token(body: CallRequest, request: Request):
    check_origin(request)
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
    # Signed here with LIVEKIT_API_SECRET; the browser only ever receives the short-lived JWT.
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


@app.get("/health")
async def health():
    # Liveness only: reveals no configuration or dependency details.
    return JSONResponse({"status": "ok"}, headers={"Cache-Control": "no-store"})


# Browsers must revalidate (a cheap 304 via ETag) so an edit never pairs new HTML with stale CSS.
NO_CACHE = {"Cache-Control": "no-cache"}


@app.get("/")
async def index():
    return FileResponse(ROOT / "index.html", headers=NO_CACHE)


@app.get("/playground")
async def playground():
    return FileResponse(ROOT / "index.html", headers=NO_CACHE)


@app.get("/{asset}")
async def asset(asset: str):
    if asset not in PUBLIC_FILES:
        raise HTTPException(404)
    return FileResponse(ROOT / asset, headers=NO_CACHE)
