from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import json

from database import get_db, init_db
from models import BatteryData, PredictionResult, User
from schemas import UserRegister, UserLogin, Token, BatteryIn
from auth import hash_password, verify_password, create_access_token, get_current_user
from ml_model import BatteryRULPredictor

app = FastAPI(title="Unified Battery System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
predictor = BatteryRULPredictor()


@app.on_event("startup")
async def startup():
    db = next(get_db())
    predictor.train(db)


# -------- AUTH --------
@app.post("/api/auth/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == user.email) | (User.username == user.username)).first():
        raise HTTPException(status_code=400, detail="User exists")

    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "registered", "user_id": db_user.id}


@app.post("/api/auth/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": db_user.id,
        "role": db_user.role
    })

    return {"access_token": token, "token_type": "bearer"}


# -------- BATTERY --------
@app.post("/api/battery-data")
def add_battery(data: BatteryIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Добавление новых данных от батареи"""
    try:
        record = BatteryData(
            voltage=data.voltage,
            current=data.current,
            temperature=data.temperature,
            capacity=data.capacity,
            cycle_number=data.cycle_number,
            battery_id=data.battery_id,
            owner_id=user.id
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # Переобучаем модель
        predictor.train(db)

        return {"status": "ok", "id": record.id, "message": "Data added successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/battery-history/{battery_id}")
def get_battery_history(
        battery_id: str,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user)
):
    """Получение исторических данных батареи"""
    battery_data = db.query(BatteryData).filter(
        BatteryData.battery_id == battery_id,
        BatteryData.owner_id == user.id
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


@app.get("/api/predict-rul/{battery_id}")
def predict_rul(
        battery_id: str,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user)
):
    """Получение предсказания RUL для батареи"""
    try:
        # Получаем данные батареи для текущего пользователя
        battery_data = db.query(BatteryData).filter(
            BatteryData.battery_id == battery_id,
            BatteryData.owner_id == user.id
        ).order_by(BatteryData.timestamp).all()

        if not battery_data:
            raise HTTPException(status_code=404, detail="No battery data found")

        # Подготовка данных для предсказания
        history = [
            {
                'voltage': r.voltage,
                'current': r.current,
                'temperature': r.temperature,
                'capacity': r.capacity,
                'cycle_number': r.cycle_number
            } for r in battery_data
        ]

        # Предсказание
        predicted_rul, confidence = predictor.predict(history)

        if predicted_rul is None:
            raise HTTPException(status_code=400, detail="Prediction failed")

        # Сохранение результата предсказания
        pred_record = PredictionResult(
            battery_id=battery_id,
            predicted_rul=predicted_rul,
            confidence=confidence,
            features=json.dumps(history[-1]),
            owner_id=user.id
        )
        db.add(pred_record)
        db.commit()

        return {
            "battery_id": battery_id,
            "predicted_rul": round(predicted_rul, 2),
            "rul": round(predicted_rul, 2),  # Добавляем для совместимости с frontend
            "confidence": round(confidence, 2),
            "current_cycle": battery_data[-1].cycle_number,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/retrain-model")
def retrain_model(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Переобучение модели"""
    try:
        success = predictor.train(db)
        return {"success": success, "message": "Model retrained successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")


@app.get("/api/health")
def health_check():
    """Проверка состояния системы"""
    return {
        "status": "healthy",
        "model_trained": predictor.is_trained,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)