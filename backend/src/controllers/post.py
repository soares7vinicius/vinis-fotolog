from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlmodel import Session, select
from src.config import UPLOAD_DIR
from src.db import get_db
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


@router.get("/posts")
def get_posts(
    user_id: int | None = Query(
        default=None,
        description="Filter posts by user ID. If provided, only posts from this user will be returned.",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="The page number to retrieve, starting from 1.",
    ),
    size: int = Query(
        default=10,
        ge=1,
        le=100,
        description="The number of posts per page.",
    ),
    db: Session = Depends(get_db),
):
    where_clause = [True] if not user_id else [Post.user_id == user_id]
    stmt = select(Post).where(*where_clause).offset((page - 1) * size).limit(size)
    posts = db.exec(stmt).all()
    return {"posts": posts, "page": page, "size": size, "total": len(posts)}


@router.post("/posts/{post_id}/like")
def like_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    liked_posts: list[int] = request.session.get("liked_posts", [])

    if post_id in liked_posts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have already liked this post",
        )

    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    post.likes += 1
    db.add(post), db.commit(), db.refresh(post)

    request.session["liked_posts"] = liked_posts + [post_id]

    return {"post_id": post.id, "likes": post.likes}
