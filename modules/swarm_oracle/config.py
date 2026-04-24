import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:latest"
    NUM_AGENTS: int = 50
    CHROMA_DB_PATH: str = "./chroma_db"
    EBPF_SOCKET_PATH: str = "/tmp/omniclaw_ebpf.sock"

    class Config:
        env_file = ".env"

settings = Settings()
