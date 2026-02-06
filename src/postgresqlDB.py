from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from typing import cast, Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Only read the URL, don't create engine yet
DATABASE_URL = cast(str, os.getenv("DATABASE_URL"))

# These will be initialized when needed
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
        
        engine = create_engine(DATABASE_URL, echo=True)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        
        # Create tables
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
    
    db = SessionLocal()  # create a new database session
    try:
        yield db          # give this session to whatever code is inside the "with" block
        db.commit()       # if everything inside "with" ran without errors, commit changes
    except Exception as e:
        db.rollback()     # if an exception happens, roll back all changes
        logger.error(f"Database session error: {e}")
        raise             # re-raise the exception so it's not silently ignored
    finally:
        db.close()        # always close the session at the end