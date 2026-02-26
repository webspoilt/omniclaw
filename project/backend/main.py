from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from routes import agents, costs, tools
from config import settings

logging.basicConfig(level=settings.log_level)

app = FastAPI(title="Agent Mission Control")

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(costs.router)
app.include_router(tools.router)

@app.get("/")
async def root():
    return {"message": "Agent Mission Control API"}
