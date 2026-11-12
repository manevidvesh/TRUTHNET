from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from app.core.config import settings

class Base(DeclarativeBase):
    pass

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# Enable SQLite foreign keys, WAL mode, and busy timeout on connection
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.close()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

def _migrate_sqlite_schema(sync_conn) -> None:
    """
    Safely applies backwards-compatible schema upgrades for existing SQLite databases.
    Preserves all existing rows, fencing counters, claims, and version histories.
    Idempotent: skips tables that already match the upgraded schema.
    """
    # Check if submission_processing_locks table exists
    result = sync_conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='submission_processing_locks';"
    )
    if not result.fetchone():
        return

    # Check if locked_by column has NOT NULL constraint (notnull == 1)
    info = sync_conn.exec_driver_sql("PRAGMA table_info(submission_processing_locks);").fetchall()
    locked_by_col = next((c for c in info if c[1] == 'locked_by'), None)
    if locked_by_col and locked_by_col[3] == 1:
        # Table was created under prior pre-change schema with NOT NULL on locked_by.
        # Migrate table to allow locked_by to be NULL for released locks while preserving all rows and tokens.
        sync_conn.exec_driver_sql("PRAGMA foreign_keys=OFF;")
        sync_conn.exec_driver_sql("""
        CREATE TABLE submission_processing_locks_migrated (
            submission_id VARCHAR(36) PRIMARY KEY,
            locked_by VARCHAR(100),
            fencing_token INTEGER NOT NULL DEFAULT 1,
            locked_at DATETIME NOT NULL,
            expires_at DATETIME NOT NULL
        );
        """)
        sync_conn.exec_driver_sql("""
        INSERT INTO submission_processing_locks_migrated (submission_id, locked_by, fencing_token, locked_at, expires_at)
        SELECT submission_id, locked_by, fencing_token, locked_at, expires_at FROM submission_processing_locks;
        """)
        sync_conn.exec_driver_sql("DROP TABLE submission_processing_locks;")
        sync_conn.exec_driver_sql("ALTER TABLE submission_processing_locks_migrated RENAME TO submission_processing_locks;")
        sync_conn.exec_driver_sql("PRAGMA foreign_keys=ON;")

async def init_db(target_engine=None) -> None:
    eng = target_engine or engine
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_sqlite_schema)
