import json
from typing import List
from fastapi import HTTPException, status
from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY


def evaluate_resume_with_gemini(pdf_bytes: bytes, requirements: List[str]) -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    Você é um assistente especialista em recrutamento e seleção.
    Analise o currículo em PDF fornecido em anexo em relação aos seguintes requisitos da vaga:
    Requisitos: {', '.join(requirements)}

    Retorne EXATAMENTE um objeto JSON com as seguintes chaves:
    - "score": Um número de 0 a 100 indicando o nível de compatibilidade.
    - "reasoning": Uma breve explicação justificando a nota atribuída.
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        return {
            "score": float(result.get("score", 0)),
            "reasoning": result.get("reasoning", "Sem justificativa fornecida.")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar currículo via IA: {str(e)}"
        )
