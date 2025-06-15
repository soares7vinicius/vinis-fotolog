from sqlmodel import SQLModel
from src.db import engine
from src.models.models import Comment, Post, User

SQLModel.metadata.create_all(bind=engine)
