from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth, dashboard, input, ai, alerts, reports
from mqtt_worker import mqtt_loop, _client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start MQTT worker on startup
    mqtt_loop(daemon=True)
    yield
    # Clean up on shutdown
    if _client:
        _client.loop_stop()
        _client.disconnect()

app = FastAPI(title="Smart Maggot Farming API", lifespan=lifespan)

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(input.router, prefix="/api/input", tags=["input"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Smart Maggot Farming API is running"}
