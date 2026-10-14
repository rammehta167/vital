import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from .db import engine, Base, SessionLocal
from .models import User
from .routers import (
    auth, readings, sos, events, contacts, devices,
    medications, reports, symptoms, summary, chat,
    emergency_id, stream, simulator_ctrl, admin
)
from simulator.simulator import global_simulator

# Create all database tables
Base.metadata.create_all(bind=engine)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    db = SessionLocal()
    try:
        # Check if users exist; if not, automatically seed
        user_count = db.query(User).count()
        if user_count == 0:
            print("[STARTUP] Empty database detected. Running initial seed data...")
            from seed.seed import run_seed
            run_seed(db)
    except Exception as e:
        print(f"[STARTUP ERROR] Auto-seeding error: {e}")
    finally:
        db.close()

    # Auto-start simulator if configured
    if os.getenv("SIMULATOR_AUTO_START", "true").lower() in ("true", "1", "yes"):
        global_simulator.start()

    yield

    # Shutdown actions
    global_simulator.stop()


app = FastAPI(
    title="AI Healthcare Companion & Smart Vital Tracker",
    description="Educational prototype software for B.Tech Major Project. Not a certified medical device.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS locked to localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(readings.router)
app.include_router(sos.router)
app.include_router(events.router)
app.include_router(contacts.router)
app.include_router(devices.router)
app.include_router(medications.router)
app.include_router(reports.router)
app.include_router(symptoms.router)
app.include_router(summary.router)
app.include_router(chat.router)
app.include_router(emergency_id.router)
app.include_router(stream.router)
app.include_router(simulator_ctrl.router)
app.include_router(admin.router)

# Mount static assets if frontend directory exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", response_class=FileResponse)
def serve_root():
    landing_file = FRONTEND_DIR / "landing.html"
    index_file = FRONTEND_DIR / "index.html"
    if landing_file.exists():
        return FileResponse(landing_file)
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h2>AI Healthcare Companion Backend Running. Frontend loading...</h2>")


@app.get("/landing", response_class=FileResponse)
@app.get("/login", response_class=FileResponse)
def serve_landing():
    landing_file = FRONTEND_DIR / "landing.html"
    if landing_file.exists():
        return FileResponse(landing_file)
    return serve_root()



@app.get("/dashboard", response_class=FileResponse)
@app.get("/app", response_class=FileResponse)
def serve_dashboard():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h2>Clinical Telemetry Dashboard loading...</h2>")


@app.get("/emergency/{token}", response_class=FileResponse)
def serve_emergency_view(token: str):
    index_file = FRONTEND_DIR / "index.html"
    return FileResponse(index_file)


@app.get("/ack/{token}", response_class=FileResponse)
def serve_ack_view(token: str):
    index_file = FRONTEND_DIR / "index.html"
    return FileResponse(index_file)

