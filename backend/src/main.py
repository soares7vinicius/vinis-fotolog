import os

from fastapi import FastAPI
from sqlmodel import SQLModel
from src.controllers.login import router as login_router
from src.controllers.post import router as post_router
from src.db import engine
from starlette.middleware.sessions import SessionMiddleware

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="chave-secreta-troque-isso")
app.include_router(login_router)
app.include_router(post_router)


SQLModel.metadata.create_all(bind=engine)
