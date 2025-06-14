from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from src.main import app, templates


@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "senha123":
        request.session["logged_in"] = True
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": "Credenciais inválidas"}
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
