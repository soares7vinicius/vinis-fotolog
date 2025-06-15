from sqlmodel import Session, create_engine
from contextlib import contextmanager

engine = create_engine(
    "sqlite:///fotolog.db", connect_args={"check_same_thread": False}
)

def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()