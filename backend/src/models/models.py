from datetime import datetime
from typing import Self
from sqlmodel import (
    SQLModel,
    Field,
    Relationship,
)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int = Field(primary_key=True, index=True)
    username: str = Field(index=True, unique=True)
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    posts: list["Post"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @classmethod
    def hash_password(cls, password: str) -> str:
        from passlib.hash import bcrypt
        return bcrypt.hash(password)




class Post(SQLModel, table=True):
    __tablename__ = "posts"
    id: int = Field(primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id")
    title: str
    filename: str
    caption: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    likes: int = Field(default=0)
    # --
    comments: list["Comment"] = Relationship(
        back_populates="post", sa_relationship_kwargs={"lazy": "selectin"}
    )
    user: User = Relationship(back_populates="posts")

class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    id: int = Field(primary_key=True, index=True)
    post_id: int = Field(foreign_key="posts.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # --
    post: Post = Relationship(back_populates="comments")
