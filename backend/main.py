from fastapi import FastAPI, Depends, HTTPException
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
    record = BatteryData(
        **data.dict(),
        owner_id=user.id
    )
    db.add(record)
    db.commit()
    predictor.train(db)
    return {"status": "ok", "id": record.id}


@app.get("/api/predict-rul/{battery_id}")
def predict(battery_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = db.query(BatteryData).filter(
        BatteryData.battery_id == battery_id,
        BatteryData.owner_id == user.id
    ).order_by(BatteryData.timestamp).all()

    if not data:
        raise HTTPException(404, "No data")

    history = [
        {
            'voltage': r.voltage,
            'current': r.current,
            'temperature': r.temperature,
            'capacity': r.capacity,
            'cycle_number': r.cycle_number
        } for r in data
    ]

    rul, conf = predictor.predict(history)

    if rul is None:
        raise HTTPException(400, "Prediction failed")

    pred_record = PredictionResult(
        battery_id=battery_id,
        predicted_rul=rul,
        confidence=conf,
        features=json.dumps(history[-1]),
        owner_id=user.id
    )
    db.add(pred_record)
    db.commit()

    return {"battery_id": battery_id, "rul": round(rul, 2), "confidence": round(conf, 2)}


@app.get("/api/health")
def health():
    return {"status": "ok", "model_trained": predictor.is_trained}