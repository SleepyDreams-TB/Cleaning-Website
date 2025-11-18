from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from typing import cast

# Variables that can be used elsewhere
DATABASE_URL = cast(str, os.getenv("DATABASE_URL"))
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    """Yields a database session and ensures it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()