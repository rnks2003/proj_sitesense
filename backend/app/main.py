from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .routers import scans, files
from .db import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SiteSense API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(scans.router)
app.include_router(files.router)

# Static files - use absolute path relative to backend directory
import os
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Serve index.html at root
from fastapi.responses import FileResponse

@app.get("/")
async def read_root():
    index_path = os.path.join(frontend_dir, "index.html")
    return FileResponse(index_path)
