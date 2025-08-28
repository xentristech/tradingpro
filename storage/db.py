import os
from typing import Optional, Any, Dict
from sqlalchemy import create_engine, Column, Integer, Float, String, Text, DateTime, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

_DB_PATH = os.getenv("DB_PATH", os.path.join("data", "trading.db"))
os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{_DB_PATH}", future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base(metadata=MetaData())

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(32), index=True)
    timeframe = Column(String(16))
    strength = Column(Float)
    payload = Column(Text)

def init():
    Base.metadata.create_all(engine)

def insert_signal(ts_iso: str, symbol: str, timeframe: str, strength: float, payload_json: str):
    ts = datetime.fromisoformat(ts_iso) if "T" in ts_iso else datetime.fromisoformat(ts_iso.replace(" ", "T"))
    with SessionLocal() as s:
        s.add(Signal(ts=ts, symbol=symbol, timeframe=timeframe, strength=strength, payload=payload_json))
        s.commit()

def last_signals(limit: int = 50):
    with SessionLocal() as s:
        return s.query(Signal).order_by(Signal.ts.desc()).limit(limit).all()
