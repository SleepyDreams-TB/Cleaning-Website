from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from typing import cast, Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = cast(str, os.getenv("DATABASE_URL"))

engine: Optional[object] = None
SessionLocal: Optional[sessionmaker] = None

def init_db():
    """Initialize database engine and create tables - called at app startup"""
    global engine, SessionLocal
    
    if engine is not None:
        return  # Already initialized
    
    try:
        if not DATABASE_URL:
            logger.warning("DATABASE_URL not set - database functionality will be unavailable")
            return
        
        engine = create_engine(
            DATABASE_URL,
            echo=True,
            pool_pre_ping=True,       # Test connection before using it (fixes Railway drops)
            pool_recycle=300,          # Recycle connections every 5 mins (before Railway kills them)
            pool_size=5,               # Max persistent connections
            max_overflow=10,           # Extra connections allowed under load
            pool_timeout=30,           # Wait up to 30s for a connection
            connect_args={
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        )
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@contextmanager
def db_session():
    """Context manager for database sessions"""
    if engine is None:
        init_db()
    
    if engine is None:
        raise RuntimeError("Database not initialized - DATABASE_URL may be missing")
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()