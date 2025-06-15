from fastapi import Depends, HTTPException, Request, status, Response
from passlib.hash import bcrypt
from pydantic import BaseModel
from sqlmodel import Session, select

from src.db import get_db
from src.models.models import User
from fastapi import APIRouter

router = APIRouter()


class LoginPayload(BaseModel):
    username: str
    password: str


def is_logged_in(request: Request):
    return request.session.get("logged_in", False)


@router.post("/login")
def login(payload: LoginPayload, request: Request, db: Session = Depends(get_db)):
    statement = select(User).where(User.username == payload.username)
    user = db.exec(statement).first()
    print(user)
    if not user or not bcrypt.verify(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    request.session["logged_in"] = True
    request.session["user_id"] = user.id
    return {"detail": "Success", "user_id": user.id}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return Response({"detail": "Success"}, status_code=status.HTTP_200_OK)
