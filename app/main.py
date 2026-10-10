from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.database.connection import Base, engine
from app.database import models  
from app.modules.auth.router import router as auth_router
from app.modules.usuarios.router import router as usuarios_router
from app.modules.vagas.router import router as vagas_router
from app.modules.candidaturas.router import router as candidaturas_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de RH com Triagem via Gemini IA")
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(vagas_router)
app.include_router(candidaturas_router)


@app.get("/", include_in_schema=False)
@app.get("/login", include_in_schema=False)
def login_page():
    return RedirectResponse("/frontend/", status_code=307)


@app.get("/cadastro", include_in_schema=False)
def registration_page():
    return RedirectResponse("/frontend/cadastro.html", status_code=307)


@app.get("/painel", include_in_schema=False)
def panel_page():
    return RedirectResponse("/frontend/painel.html", status_code=307)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount(
    "/frontend",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend",
)
