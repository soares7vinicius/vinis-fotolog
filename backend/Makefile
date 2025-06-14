run:
	poetry run uvicorn fotolog.main:app --host 0.0.0.0 --port 8000 --reload --workers 1 --log-level debug

install:
	poetry install

shell:
	poetry shell

init-db:
	poetry run python -c "from fotolog.models import Base, engine; Base.metadata.create_all(bind=engine)"