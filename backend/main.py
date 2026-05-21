from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID
import os
from google import genai

from .database import engine, get_db
from .models import Base, Atividade, DailyReport
from .auth import get_current_user_id

# Ensure the database tables are created and synchronized with Supabase Cloud on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FocusTrack AI Engine",
    description="The fast, Supabase-powered backend for FocusTrack AI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class AtividadeCreate(BaseModel):
    categoria: str
    descricao: str
    data: date
    inicio: datetime
    fim: datetime
    nivel_foco: int

class AtividadeOut(AtividadeCreate):
    id: int
    user_id: UUID

    model_config = {"from_attributes": True}

class DailyReportOut(BaseModel):
    id: int
    data: date
    resumo_ia: str
    user_id: UUID

    model_config = {"from_attributes": True}

@app.get("/")
def health_check():
    return {"status": "ok", "message": "FocusTrack AI backend is running and connected."}

@app.post("/api/atividade", response_model=AtividadeOut)
def create_atividade(
    atividade: AtividadeCreate, 
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    db_atividade = Atividade(
        user_id=user_id,
        categoria=atividade.categoria,
        descricao=atividade.descricao,
        data=atividade.data,
        inicio=atividade.inicio,
        fim=atividade.fim,
        nivel_foco=atividade.nivel_foco
    )
    db.add(db_atividade)
    db.commit()
    db.refresh(db_atividade)
    return db_atividade

@app.get("/api/atividade", response_model=List[AtividadeOut])
def get_atividades(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    return db.query(Atividade).filter(Atividade.user_id == user_id).all()

@app.post("/api/analisar", response_model=DailyReportOut)
def analisar_dia(
    target_date: date,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    import uuid
    # Strictly cast the JWT sub string into a psycopg2 UUID object so SQLAlchemy filters cleanly
    user_uuid = uuid.UUID(user_id)

    # Retrieve activities for the specific user and date
    atividades = db.query(Atividade).filter(
        Atividade.user_id == user_uuid,
        Atividade.data == target_date
    ).all()

    if not atividades:
        # Returning a 400 Bad Request instead of a 404 Not Found to prevent misleading routing errors on the frontend
        raise HTTPException(status_code=400, detail="Sem atividades cadastradas nesta data para analisar.")

    # ----------------------------------------------------
    # Integrate Google GenAI Gemini 1.5-Flash
    # ----------------------------------------------------
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Google API Key ausente.")

    client = genai.Client(api_key=api_key)

    activities_text = "\n".join([
        f"- Categoria: {a.categoria} | Descrição: {a.descricao} | Foco: {a.nivel_foco}/10" 
        for a in atividades
    ])

    prompt_content = f"""
Atividades do dia ({target_date}):
{activities_text}

Por favor, atue como um Mentor de Produtividade ("Jarbis"). 
Analise as atividades da sessão acima e forneça um feedback construtivo nativamente em português do Brasil.
Concentre-se no progresso do usuário em direção à excelência, foco e produtividade. Baseie sua resposta em como essas métricas e esforços diários ajudam a alcançar seus objetivos pessoais e profissionais.
Seja conciso (1 ou 2 parágrafos curtos no máximo), estratégico e sempre conclua com um conselho acionável, direto e prático para as próximas horas.
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_content,
        )
        resumo_texto = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno de geração Gemini AI: {str(e)}")

    # Construct the persistent record in Supabase
    db_report = DailyReport(
        user_id=user_uuid,
        data=target_date,
        resumo_ia=resumo_texto
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return db_report

@app.delete("/api/atividade/{atividade_id}")
def delete_atividade(
    atividade_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    atividade = db.query(Atividade).filter(Atividade.id == atividade_id).first()
    if not atividade:
        raise HTTPException(status_code=404, detail="Activity not found.")
    
    # Multitenancy security check
    if str(atividade.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this activity.")
    
    db.delete(atividade)
    db.commit()
    return {"status": "success", "message": "Activity deleted successfully."}

