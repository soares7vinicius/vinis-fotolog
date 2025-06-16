import os
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from sqlmodel import Session, select
from src.config import UPLOAD_DIR
from src.db import get_db
from src.models.api_models.post import GetPostsPayload
from src.models.models import ImageMetadata, Post
from src.utils.image import SUPPORTED_FORMATS, ImageProcessor

router = APIRouter()


@router.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(
    request: Request,
    title: str = Form(...),
    caption: str = Form(...),
    image: UploadFile = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("logged_in"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be logged in to create a post",
        )

    ip = ImageProcessor(image.file.read(), image.filename)

    if not ip.is_supported():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format. Please upload any of the following formats: {', '.join(SUPPORTED_FORMATS)}",
        )

    ip.to_jpeg(inplace=True)
    ip.resize(max_size=2048, inplace=True)
    filename = ip.to_file(UPLOAD_DIR)

    user_id = request.session.get("user_id")
    post = Post(
        title=title,
        caption=caption,
        filename=filename,
        user_id=user_id,
        image_metadata=ImageMetadata(**ip.metadata),
    )
    db.add(post), db.commit(), db.refresh(post)
    return {
        "post": post,
        "image_metadata": post.image_metadata,
        "message": "Post created successfully",
    }


@router.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    return post


@router.get("/posts", response_model=list[Post])
def get_posts(payload: GetPostsPayload, db: Session = Depends(get_db)):
    where_clause = [True] if not payload.user_id else [Post.user_id == payload.user_id]
    stmt = (
        select(Post)
        .where(*where_clause)
        .offset((payload.pagination.page - 1) * payload.pagination.size)
        .limit(payload.pagination.size)
    )
    posts = db.exec(stmt).all()
    return posts
