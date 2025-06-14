run:
	poetry run uvicorn fotolog.main:app --host 0.0.0.0 --port 8000 --reload --workers 1 --log-level debug

install:
	poetry install

shell:
	poetry shell

init-db:
	PYTHONPATH=backend poetry run python -c "from src.models import Base; from src.db import engine; Base.metadata.create_all(bind=engine)"