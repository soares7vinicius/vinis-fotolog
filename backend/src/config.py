import os

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "change-me")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "static/uploads")
