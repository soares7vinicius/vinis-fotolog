from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import shutil
import os

from sqlmodel import SQLModel
from starlette.middleware.sessions import SessionMiddleware

from src.models.models import Comment, Post
from src.db import engine, get_db

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="chave-secreta-troque-isso")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SQLModel.metadata.create_all(bind=engine)


def is_logged_in(request: Request):
    return request.session.get("logged_in", False)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return templates.TemplateResponse(
        "index.html", {"request": request, "posts": posts}
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_get(request: Request, db: Session = Depends(get_db)):
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=302)
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return templates.TemplateResponse(
        "admin.html", {"request": request, "posts": posts}
    )


@app.post("/admin")
def admin_post(
    request: Request,
    title: str = Form(...),
    caption: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not is_logged_in(request):
        raise HTTPException(status_code=403)

    filename = photo.filename
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    post = Post(title=title, caption=caption, filename=filename)
    db.add(post)
    db.commit()
    return RedirectResponse("/admin", status_code=302)


@app.get("/delete/{post_id}")
def delete_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_logged_in(request):
        raise HTTPException(status_code=403)
    post = db.query(Post).get(post_id)
    if post:
        try:
            os.remove(os.path.join(UPLOAD_DIR, post.filename))
        except:
            pass
        db.delete(post)
        db.commit()
    return RedirectResponse("/admin", status_code=302)


@app.post("/like/{post_id}")
def like_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).get(post_id)
    if post:
        post.likes += 1
        db.commit()
    return RedirectResponse("/", status_code=302)


@app.post("/comment/{post_id}")
def comment_post(post_id: int, content: str = Form(...), db: Session = Depends(get_db)):
    comment = Comment(post_id=post_id, content=content)
    db.add(comment)
    db.commit()
    return RedirectResponse("/", status_code=302)


@app.get("/edit_comment/{comment_id}", response_class=HTMLResponse)
def edit_comment(comment_id: int, request: Request, db: Session = Depends(get_db)):
    comment = db.query(Comment).get(comment_id)
    if not comment:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "edit_comment.html", {"request": request, "comment": comment}
    )


@app.post("/edit_comment/{comment_id}")
def edit_comment_post(
    comment_id: int, content: str = Form(...), db: Session = Depends(get_db)
):
    comment = db.query(Comment).get(comment_id)
    if comment:
        comment.content = content
        db.commit()
    return RedirectResponse("/", status_code=302)


@app.get("/delete_comment/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.query(Comment).get(comment_id)
    if comment:
        db.delete(comment)
        db.commit()
    return RedirectResponse("/", status_code=302)


@app.post("/like_once/{post_id}")
def like_post_once(post_id: int, request: Request, db: Session = Depends(get_db)):
    liked = request.session.get(f"liked_{post_id}", False)
    if not liked:
        post = db.query(Post).get(post_id)
        if post:
            post.likes += 1
            db.commit()
            request.session[f"liked_{post_id}"] = True
    return RedirectResponse("/", status_code=302)
