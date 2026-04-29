from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import PrimarySwitchRequest, TaskRequest
from app.orchestrator import OrchestratorService
from app.registry import RegistryService

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "registry.json"


@asynccontextmanager
async def lifespan(application: FastAPI):
    if not DATA_PATH.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        registry.save(registry.load())
    yield


app = FastAPI(title="LLM Orchestrator Dashboard", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
registry = RegistryService(DATA_PATH)
orchestrator = OrchestratorService(registry)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    state = registry.load()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "state": state,
            "primary": registry.get_active_primary(),
            "workers": registry.list_workers(),
        },
    )


@app.get("/api/state")
def get_state():
    return registry.load()


@app.get("/api/health")
def health_check():
    state = registry.load()
    primary = registry.get_active_primary()
    return {
        "ok": True,
        "models": len(state.models),
        "platforms": len(state.platforms),
        "primary": primary.id if primary else None,
    }


@app.get("/api/models")
def list_models():
    state = registry.load()
    return state.models


@app.post("/api/orchestrate")
def orchestrate(request: TaskRequest):
    try:
        return orchestrator.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/failover")
def trigger_failover(reason: str = "manual failover"):
    event = registry.promote_backup(reason)
    if event is None:
        raise HTTPException(status_code=400, detail="No backup available")
    return event


@app.post("/api/primary/switch")
def switch_primary(request: PrimarySwitchRequest):
    model = registry.set_primary(request.model_id, request.reason)
    if model is None:
        raise HTTPException(status_code=400, detail="Model not found or disabled")
    return model
