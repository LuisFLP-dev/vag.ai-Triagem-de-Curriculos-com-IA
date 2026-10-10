import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sistema_rh.db")

if not SECRET_KEY:
    raise ValueError("ERRO: A variável JWT_SECRET_KEY não foi encontrada no arquivo .env!")

if not GEMINI_API_KEY:
    raise ValueError("ERRO: A variável GEMINI_API_KEY não foi encontrada no arquivo .env!")

