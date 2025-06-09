from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///fotolog.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    filename = Column(String(200))
    caption = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)
    comments = relationship("Comment", back_populates="post", cascade="all, delete")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    post = relationship("Post", back_populates="comments")
