from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db
from app.routers import pest, disease, climate


app = FastAPI(title="Agri AI Services", version="1.0")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(pest.router)
app.include_router(disease.router)
app.include_router(climate.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "agri-ai"}
