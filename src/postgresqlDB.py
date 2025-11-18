from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from typing import cast
from contextlib import contextmanager

# Variables that can be used elsewhere
DATABASE_URL = cast(str, os.getenv("DATABASE_URL"))
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(bind=engine)

@contextmanager
def db_session():
    db = SessionLocal()  # create a new database session
    try:
        yield db          # give this session to whatever code is inside the "with" block
        db.commit()       # if everything inside "with" ran without errors, commit changes
    except:
        db.rollback()     # if an exception happens, roll back all changes
        raise             # re-raise the exception so it’s not silently ignored
    finally:
        db.close()        # always close the session at the end
