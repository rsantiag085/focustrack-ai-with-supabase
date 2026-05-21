from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

class Atividade(Base):
    __tablename__ = "atividades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    categoria = Column(String, index=True)
    descricao = Column(String)
    data = Column(Date, index=True)
    inicio = Column(DateTime)
    fim = Column(DateTime)
    nivel_foco = Column(Integer)

class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    data = Column(Date, index=True)
    resumo_ia = Column(Text)
