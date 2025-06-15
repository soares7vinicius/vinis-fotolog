from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from sqlmodel import Session, select
from src.db import get_db
from src.models.api_models.login import LoginPayload
from src.models.models import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/login")
def login(payload: LoginPayload, request: Request, db: Session = Depends(get_db)):
    statement = select(User).where(User.username == payload.username)
    user = db.exec(statement).first()
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
    return {"detail": "Success"}
