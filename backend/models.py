from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()


class BatteryData(Base):
    __tablename__ = "battery_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    voltage = Column(Float)
    current = Column(Float)
    temperature = Column(Float)
    capacity = Column(Float)
    cycle_number = Column(Integer)
    battery_id = Column(String, index=True)


class PredictionResult(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    battery_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    predicted_rul = Column(Float)
    confidence = Column(Float)
    features = Column(String)  # JSON string of input features