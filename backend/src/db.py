from contextlib import contextmanager

from sqlmodel import Session, create_engine

engine = create_engine(
    "sqlite:///fotolog.db", connect_args={"check_same_thread": False}
)


def get_db(override_engine=None):
    db = Session(bind=override_engine) if override_engine else Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
