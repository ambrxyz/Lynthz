"""
Lynthz API — FastAPI backend
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_base = Path(__file__).parent.parent
for _env in [_base / ".env", Path(".env"), Path("../.env")]:
    if _env.exists():
        load_dotenv(dotenv_path=_env, override=True)
        break

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.db import supabase

app = FastAPI(title="Lynthz", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_agent = None

def get_agent():
    global _agent
    if _agent is None:
        from src.agent import Agent
        _agent = Agent()
    return _agent


# ── Auth Models ──────────────────────────────────────────────
class AuthRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


# ── Supabase helpers ─────────────────────────────────────────
async def save_message(user_id: str, role: str, content: str, model: str = None):
    try:
        supabase.table("messages").insert({
            "user_id": user_id,
            "role": role,
            "content": content,
            "model": model
        }).execute()
    except Exception as e:
        print(f"DB save error: {e}")


# ── Static files ─────────────────────────────────────────────
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    html_file = static_dir / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Lynthz API running</h1>")


# ── Auth endpoints ───────────────────────────────────────────
@app.post("/api/auth/signup")
async def signup(request: AuthRequest):
    try:
        result = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "name": request.name or request.email
                }
            }
        })

        user = result.user

        if user:
            supabase.table("profiles").upsert({
                "id": user.id,
                "email": request.email,
                "name": request.name or request.email
            }).execute()

            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": request.email,
                    "name": request.name or request.email
                }
            }

        return {"success": False, "error": "Signup failed. No user returned."}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/auth/login")
async def login(request: AuthRequest):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        user = result.user
        session = result.session

        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.user_metadata.get("name", user.email)
            },
            "session": {
                "access_token": session.access_token if session else None
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/auth/logout")
async def logout():
    return {"success": True}


# ── WebSocket chat ───────────────────────────────────────────
@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    await ws.accept()

    try:
        agent = get_agent()
    except Exception as e:
        await ws.send_json({"type": "error", "message": f"Startup error: {str(e)}"})
        await ws.close()
        return

    try:
        while True:
            raw = await ws.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            message = data.get("message", "").strip()
            model_key = data.get("model") or None

            # Real user_id from frontend after login
            user_id = data.get("user_id") or "00000000-0000-0000-0000-000000000001"

            if not message:
                continue

            await save_message(user_id, "user", message, model_key)

            full_response = ""
            used_model = model_key

            try:
                async for chunk in agent.respond(message, model_key):
                    await ws.send_json(chunk)

                    if chunk.get("type") == "model_info":
                        used_model = chunk.get("model", model_key)

                    if chunk.get("type") == "token":
                        full_response += chunk.get("content", "")

            except Exception as e:
                await ws.send_json({"type": "error", "message": str(e)})
                await ws.send_json({"type": "done"})
                continue

            if full_response:
                await save_message(user_id, "assistant", full_response, used_model)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")


# ── REST endpoints ───────────────────────────────────────────
@app.get("/api/models")
async def get_models():
    from src.llm_hub import LLMHub
    hub = LLMHub()
    return JSONResponse({"models": hub.get_models_info()})


@app.get("/api/memory")
async def get_memory():
    agent = get_agent()
    return JSONResponse(agent.get_memory_snapshot())


@app.post("/api/clear")
async def clear_conversation():
    agent = get_agent()
    agent.clear_conversation()
    return JSONResponse({"status": "cleared"})


@app.get("/api/health")
async def health():
    keys = {
        "GROQ_API_KEY": bool(os.getenv("GROQ_API_KEY")),
        "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY")),
        "TAVILY_API_KEY": bool(os.getenv("TAVILY_API_KEY")),
        "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_SERVICE_KEY": bool(os.getenv("SUPABASE_SERVICE_KEY")),
    }
    return {
        "status": "ok",
        "name": "Lynthz",
        "version": "3.0.0",
        "keys_loaded": keys
    }


@app.get("/api/history/{user_id}")
async def get_history(user_id: str):
    try:
        result = supabase.table("messages")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at")\
            .execute()

        return JSONResponse({"messages": result.data})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/history")
async def get_history_default():
    try:
        user_id = "00000000-0000-0000-0000-000000000001"

        result = supabase.table("messages")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at")\
            .execute()

        return JSONResponse({"messages": result.data})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)