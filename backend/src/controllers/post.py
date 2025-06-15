import os
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from sqlmodel import Session, select
from src.db import get_db
from src.models.api_models.post import GetPostsPayload
from src.models.models import Post
from src.utils.image import (
    SUPPORTED_FORMATS,
    any_to_jpeg,
    get_image_metadata,
    is_supported_format,
    resize_image,
    write_image_to_file,
)

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

    if not is_supported_format(image.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format. Please upload any of the following formats: {', '.join(SUPPORTED_FORMATS)}",
        )

    image_bytes = image.file.read()
    metadata = get_image_metadata(image_bytes)

    image_bytes = any_to_jpeg(image_bytes, image.filename)
    image_bytes = resize_image(image_bytes, max_size=2048)

    filename = f"{uuid4().hex}.jpg"
    filepath = f"static/uploads/{filename}"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    write_image_to_file(image_bytes, filepath)

    user_id = request.session.get("user_id")
    post = Post(
        title=title,
        caption=caption,
        filename=filename,
        user_id=user_id,
    )
    db.add(post), db.commit(), db.refresh(post)
    return {
        "detail": "Post created successfully",
        "post_id": post.id,
        "filename": filename,
        "metadata": metadata,
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
