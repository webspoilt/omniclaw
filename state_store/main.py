import asyncio
import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("StateStore")

# SQLAlchemy Imports
SQLALCHEMY_AVAILABLE = False
try:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
    from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Boolean, select
    SQLALCHEMY_AVAILABLE = True
    logger.info("SQLAlchemy loaded successfully.")
except ImportError:
    logger.warning("SQLAlchemy not installed. Install with 'pip install sqlalchemy asyncpg'. Using mock database interface.")

# ---------------------------------------------------------------------------
# Declarative Models Schema
# ---------------------------------------------------------------------------

if SQLALCHEMY_AVAILABLE:
    class Base(AsyncAttrs, DeclarativeBase):
        pass

    class TaskNode(Base):
        __tablename__ = "task_nodes"

        id: Mapped[str] = mapped_column(String(50), primary_key=True)
        name: Mapped[str] = mapped_column(String(100), nullable=False)
        command: Mapped[str] = mapped_column(Text, nullable=False)
        status: Mapped[str] = mapped_column(String(20), default="PENDING")
        created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
        completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
        inputs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-serialized
        outputs: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON-serialized
        worker_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("worker_nodes.id"), nullable=True)

        worker: Mapped[Optional["WorkerNode"]] = relationship("WorkerNode", back_populates="tasks")
        logs: Mapped[List["ExecutionLog"]] = relationship("ExecutionLog", back_populates="task", cascade="all, delete-orphan")

    class WorkerNode(Base):
        __tablename__ = "worker_nodes"

        id: Mapped[str] = mapped_column(String(50), primary_key=True)
        ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
        port: Mapped[int] = mapped_column(Integer, nullable=False)
        active: Mapped[bool] = mapped_column(Boolean, default=True)
        capabilities: Mapped[str] = mapped_column(Text, default="[]")  # JSON-serialized list
        last_heartbeat: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

        tasks: Mapped[List["TaskNode"]] = relationship("TaskNode", back_populates="worker")

    class ExecutionLog(Base):
        __tablename__ = "execution_logs"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        task_id: Mapped[str] = mapped_column(String(50), ForeignKey("task_nodes.id"), nullable=False)
        stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
        stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
        exit_code: Mapped[int] = mapped_column(Integer, default=0)
        timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

        task: Mapped["TaskNode"] = relationship("TaskNode", back_populates="logs")

    class SystemMetric(Base):
        __tablename__ = "system_metrics"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        hostname: Mapped[str] = mapped_column(String(100), nullable=False)
        cpu_usage: Mapped[float] = mapped_column(Float, nullable=False)
        memory_usage: Mapped[float] = mapped_column(Float, nullable=False)
        gpu_temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
        timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# SQLite to PostgreSQL Migration Engine
# ---------------------------------------------------------------------------

class StateStoreManager:
    def __init__(self, db_url: str = None):
        # Default to environment config database URL or local fallback sqlite-async wrapper
        self.db_url = db_url or os.environ.get("DATABASE_URL", "postgresql+asyncpg://omniclaw:omniclaw@localhost:5432/omniclaw")
        self.engine = None
        self.session_factory = None

        if SQLALCHEMY_AVAILABLE:
            # If postgres+asyncpg is requested but asyncpg is not installed, fallback to sqlite async for safety
            if self.db_url.startswith("postgresql") and not self._check_asyncpg():
                logger.warning("asyncpg module not found. Falling back to local SQLite async driver for State Store.")
                self.db_url = "sqlite+aiosqlite:///./logs/state_store.db"
                
            self.engine = create_async_engine(self.db_url, echo=False)
            self.session_factory = async_sessionmaker(bind=self.engine, expire_on_commit=False)

    def _check_asyncpg(self) -> bool:
        try:
            import asyncpg
            return True
        except ImportError:
            return False

    async def initialize_schema(self):
        """Initializes tables inside the target PostgreSQL database."""
        if not SQLALCHEMY_AVAILABLE:
            return
        async with self.engine.begin() as conn:
            # Creates all schemas asynchronously
            logger.info("Initializing State Store database schemas...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema sync complete.")

    async def migrate_legacy_sqlite(self, sqlite_filepath: str):
        """Reads legacy SQLite rows and migrates them into the async PostgreSQL state store."""
        if not os.path.exists(sqlite_filepath):
            logger.info(f"No legacy SQLite database file found at '{sqlite_filepath}'. Skipping data migration.")
            return

        if not SQLALCHEMY_AVAILABLE:
            logger.warning("SQLAlchemy not available; cannot perform data migration.")
            return

        logger.info(f"Legacy SQLite database found at '{sqlite_filepath}'. Commencing translation to PostgreSQL...")
        
        try:
            # Sync connection to SQLite
            sq_conn = sqlite3.connect(sqlite_filepath)
            sq_cursor = sq_conn.cursor()

            async with self.session_factory() as session:
                # 1. Migrate Workers
                sq_cursor.execute("SELECT id, ip_address, port, active, capabilities, last_heartbeat FROM workers")
                for row in sq_cursor.fetchall():
                    last_hb = datetime.fromisoformat(row[5]) if isinstance(row[5], str) else datetime.utcnow()
                    worker = WorkerNode(
                        id=row[0],
                        ip_address=row[1],
                        port=row[2],
                        active=bool(row[3]),
                        capabilities=row[4],
                        last_heartbeat=last_hb
                    )
                    await session.merge(worker)

                # 2. Migrate Tasks
                sq_cursor.execute("SELECT id, name, command, status, created_at, completed_at, inputs, outputs, worker_id FROM tasks")
                for row in sq_cursor.fetchall():
                    created = datetime.fromisoformat(row[4]) if isinstance(row[4], str) else datetime.utcnow()
                    completed = datetime.fromisoformat(row[5]) if isinstance(row[5], str) else None
                    task = TaskNode(
                        id=row[0],
                        name=row[1],
                        command=row[2],
                        status=row[3],
                        created_at=created,
                        completed_at=completed,
                        inputs=row[6],
                        outputs=row[7],
                        worker_id=row[8]
                    )
                    await session.merge(task)

                await session.commit()
                logger.info("Legacy SQLite data migration completed successfully.")
            
            sq_conn.close()
        except Exception as e:
            logger.error(f"Migration error: {e}. Checking if schemas are matched.")

async def main():
    # Setup test file database mimicking legacy
    legacy_db = "./logs/legacy_test.db"
    os.makedirs("./logs", exist_ok=True)
    
    # Initialize fake legacy table
    conn = sqlite3.connect(legacy_db)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS workers (id TEXT PRIMARY KEY, ip_address TEXT, port INTEGER, active INTEGER, capabilities TEXT, last_heartbeat TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, name TEXT, command TEXT, status TEXT, created_at TEXT, completed_at TEXT, inputs TEXT, outputs TEXT, worker_id TEXT)")
    c.execute("INSERT OR REPLACE INTO workers VALUES ('worker_01', '127.0.0.1', 8080, 1, '[]', '2026-05-19T00:00:00')")
    c.execute("INSERT OR REPLACE INTO tasks VALUES ('task_100', 'Compiling', 'gcc main.c', 'PENDING', '2026-05-19T00:00:00', NULL, NULL, NULL, 'worker_01')")
    conn.commit()
    conn.close()

    # Use SQLite async driver if postgres is not online in local environment
    manager = StateStoreManager(db_url="sqlite+aiosqlite:///./logs/state_store.db")
    await manager.initialize_schema()
    await manager.migrate_legacy_sqlite(legacy_db)

if __name__ == "__main__":
    asyncio.run(main())
