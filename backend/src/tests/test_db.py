import pytest
from src.db import get_db


def test_get_db(engine):
    db = next(get_db(engine))

    assert db is not None
    assert hasattr(db, "execute")
    assert hasattr(db, "commit")
    assert hasattr(db, "close")
    assert db.bind is not None
    assert db.bind.engine == engine
