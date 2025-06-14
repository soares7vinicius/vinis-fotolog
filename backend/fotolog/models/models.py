from datetime import datetime
from sqlmodel import (
    SQLModel,
    Field,
    Relationship,
)


class Post(SQLModel, table=True):
    __tablename__ = "posts"
    id: int = Field(primary_key=True, index=True)
    title: str
    filename: str
    caption: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    likes: int = Field(default=0)
    comments: list["Comment"] = Relationship(
        back_populates="post", sa_relationship_kwargs={"lazy": "selectin"}
    )


class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    id: int = Field(primary_key=True, index=True)
    post_id: int = Field(foreign_key="posts.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    post: Post = Relationship(back_populates="comments")
