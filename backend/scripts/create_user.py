from src.models.models import User
from src.db import get_db

def create_user(username: str, password: str):
    with get_db() as db:
        user = User(username=username, password=User.hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python create_user.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    user = create_user(username, password)
    print(f"User created: {user.username} (ID: {user.id})")