import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.models import Base
from src.db import engine

Base.metadata.create_all(bind=engine)