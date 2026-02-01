from sqlalchemy import Column, Integer, Float, DateTime, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Изменено на Integer
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="USER")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BatteryData(Base):
    __tablename__ = "battery_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    voltage = Column(Float)
    current = Column(Float)
    temperature = Column(Float)
    capacity = Column(Float)
    cycle_number = Column(Integer)
    battery_id = Column(String(255), index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class PredictionResult(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    battery_id = Column(String(255), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    predicted_rul = Column(Float)
    confidence = Column(Float)
    features = Column(String(1000))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)