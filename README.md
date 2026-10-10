Projeto acadêmico de recrutamento e seleção com FastAPI, SQLite, Gemini e frontend em HTML, JavaScript e Tailwind CSS.

-Pré-requisitos:
* Python e pip instalados. O ambiente de desenvolvimento utiliza Python 3.14.
* Chave de API do Gemini.
* Internet para instalar dependências, carregar o Tailwind via CDN e analisar currículos.

1. Criar o ambiente virtual
#python -m venv .venv

2. Instalar as dependências
#.\.venv\Scripts\python.exe -m pip install -r requirements.txt

3. Configurar o arquivo .env

Crie um arquivo chamado .env na raiz do projeto:

JWT_SECRET_KEY=SUBSTITUA_POR_UMA_CHAVE_ALEATORIA
GEMINI_API_KEY=SUBSTITUA_PELA_SUA_CHAVE_GEMINI
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=sqlite:///./sistema_rh.db

JWT_SECRET_KEY e GEMINI_API_KEY são obrigatórias para iniciar a aplicação.

4. Iniciar a API e o frontend
.\.venv\Scripts\python.exe -m uvicorn projeto1:app --reload

5. Acessar no navegador

| Recurso | Endereço |
| --- | --- |
| Página inicial e login | http://127.0.0.1:8000/ |
| Frontend | http://127.0.0.1:8000/frontend/ |
| Cadastro | http://127.0.0.1:8000/frontend/cadastro.html |
| Painel após login | http://127.0.0.1:8000/frontend/painel.html |
| Swagger da API | http://127.0.0.1:8000/docs |
