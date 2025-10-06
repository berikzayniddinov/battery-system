import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import BatteryData

# Инициализируем базу
init_db()

# Загружаем CSV
csv_path = "Battery_RUL.csv"
df = pd.read_csv(csv_path)

print("📊 Колонки в датасете:", list(df.columns))
print(df.head(3))

# Переименуем колонки под понятные имена
df.rename(columns={
    "Cycle_Index": "cycle_number",
    "Discharge Time (s)": "discharge_time_s",
    "Decrement 3.6-3.4V (s)": "decrement_36_34_s",
    "Max. Voltage Dischar. (V)": "max_voltage_discharge_v",
    "Min. Voltage Charg. (V)": "min_voltage_charge_v",
    "Time at 4.15V (s)": "time_at_4_15v_s",
    "Time constant current (s)": "time_constant_current_s",
    "Charging time (s)": "charging_time_s",
    "RUL": "rul"
}, inplace=True)

# Добавляем фиктивный battery_id (если в датасете его нет)
df["battery_id"] = "B001"

# Проверим новые имена
print("\n🧩 После переименования:", list(df.columns))

# Открываем сессию
db: Session = SessionLocal()

# Загружаем данные
for _, row in df.iterrows():
    record = BatteryData(
        battery_id=row["battery_id"],
        cycle_number=int(row["cycle_number"]),
        voltage=float(row["max_voltage_discharge_v"]),
        current=0.0,  # нет в датасете
        temperature=25.0,  # можно фиксировать
        capacity=float(row["discharge_time_s"]),  # условно примем как "capacity"
    )
    db.add(record)

db.commit()
db.close()

print(f"\n✅ Загружено {len(df)} записей в таблицу battery_data")
