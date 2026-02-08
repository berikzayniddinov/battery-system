from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
import json

from database import get_db, init_db
from models import BatteryData, PredictionResult
from ml_model import BatteryRULPredictor

app = FastAPI(title="Battery RUL Prediction System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация БД и модели
init_db()
predictor = BatteryRULPredictor()


@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    predictor.train(db)


@app.post("/api/battery-data")
async def add_battery_data(
        data: dict,
        db: Session = Depends(get_db)
):
    """Добавление новых данных от батареи"""
    try:
        battery_record = BatteryData(
            voltage=data['voltage'],
            current=data['current'],
            temperature=data['temperature'],
            capacity=data['capacity'],
            cycle_number=data['cycle_number'],
            battery_id=data.get('battery_id', 'default')
        )

        db.add(battery_record)
        db.commit()
        db.refresh(battery_record)

        predictor.train(db)

        return {"message": "Data added successfully", "id": battery_record.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/predict-rul/{battery_id}")
async def predict_rul(
        battery_id: str,
        db: Session = Depends(get_db)
):
    """Получение предсказания RUL для батареи"""
    try:
        # Получение исторических данных батареи
        battery_data = db.query(BatteryData).filter(
            BatteryData.battery_id == battery_id
        ).order_by(BatteryData.timestamp).all()

        if not battery_data:
            raise HTTPException(status_code=404, detail="Battery data not found")

        # Подготовка данных для предсказания
        data_for_prediction = []
        for record in battery_data:
            data_for_prediction.append({
                'voltage': record.voltage,
                'current': record.current,
                'temperature': record.temperature,
                'capacity': record.capacity,
                'cycle_number': record.cycle_number
            })

        # Предсказание
        predicted_rul, confidence = predictor.predict(data_for_prediction)

        if predicted_rul is None:
            raise HTTPException(status_code=400, detail="Prediction failed")

        # Сохранение результата предсказания
        prediction_record = PredictionResult(
            battery_id=battery_id,
            predicted_rul=predicted_rul,
            confidence=confidence,
            features=json.dumps(data_for_prediction[-1])  # Последние измерения
        )

        db.add(prediction_record)
        db.commit()

        return {
            "battery_id": battery_id,
            "predicted_rul": round(predicted_rul, 2),
            "confidence": round(confidence, 2),
            "current_cycle": battery_data[-1].cycle_number,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/battery-history/{battery_id}")
async def get_battery_history(
        battery_id: str,
        db: Session = Depends(get_db)
):
    """Получение исторических данных батареи"""
    battery_data = db.query(BatteryData).filter(
        BatteryData.battery_id == battery_id
    ).order_by(BatteryData.timestamp).all()

    return {
        "battery_id": battery_id,
        "data": [
            {
                "timestamp": record.timestamp.isoformat(),
                "voltage": record.voltage,
                "current": record.current,
                "temperature": record.temperature,
                "capacity": record.capacity,
                "cycle_number": record.cycle_number
            }
            for record in battery_data
        ]
    }


@app.post("/api/retrain-model")
async def retrain_model(db: Session = Depends(get_db)):
    """Переобучение модели"""
    success = predictor.train(db)
    return {"success": success, "message": "Model retrained"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "model_trained": predictor.is_trained}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)