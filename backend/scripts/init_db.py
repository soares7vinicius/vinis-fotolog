from sqlmodel import SQLModel
from src.db import engine
from src.models.models import User, Post, Comment

SQLModel.metadata.create_all(bind=engine)