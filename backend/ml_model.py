import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from sqlalchemy.orm import Session
from models import BatteryData
import json


class BatteryRULPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_features(self, data):
        """Подготовка признаков для модели"""
        features = []
        for battery_id in data['battery_id'].unique():
            battery_data = data[data['battery_id'] == battery_id]

            # Признаки на основе деградации емкости
            capacity_data = battery_data['capacity'].values
            cycles = len(capacity_data)

            if cycles >= 3:
                # Тренд деградации
                x = np.arange(cycles)
                slope = np.polyfit(x, capacity_data, 1)[0]

                # Статистические признаки
                mean_capacity = np.mean(capacity_data)
                std_capacity = np.std(capacity_data)
                capacity_fade = capacity_data[0] - capacity_data[-1]

                # Признаки из последнего измерения
                last_measurement = battery_data.iloc[-1]

                feature_vector = [
                    cycles,
                    slope,
                    mean_capacity,
                    std_capacity,
                    capacity_fade,
                    last_measurement['voltage'],
                    last_measurement['current'],
                    last_measurement['temperature'],
                    last_measurement['capacity']
                ]

                # Целевая переменная - оставшиеся циклы (для обучения)
                # В реальных данных это должно быть известно из исторических данных
                remaining_cycles = max(0, 1000 - cycles)  # Примерная максимальная жизнь

                features.append((feature_vector, remaining_cycles))

        return features

    def train(self, db: Session):
        """Обучение модели на исторических данных"""
        try:
            # Получение данных из БД (все данные для обучения)
            battery_data = db.query(BatteryData).all()

            if len(battery_data) < 10:
                print("Недостаточно данных для обучения")
                return False

            # Конвертация в DataFrame
            data_dict = []
            for record in battery_data:
                data_dict.append({
                    'battery_id': record.battery_id,
                    'cycle_number': record.cycle_number,
                    'voltage': record.voltage,
                    'current': record.current,
                    'temperature': record.temperature,
                    'capacity': record.capacity
                })

            df = pd.DataFrame(data_dict)

            # Подготовка признаков
            features_data = self.prepare_features(df)

            if len(features_data) == 0:
                print("Не удалось подготовить признаки")
                return False

            X = [item[0] for item in features_data]
            y = [item[1] for item in features_data]

            # Масштабирование признаков
            X_scaled = self.scaler.fit_transform(X)

            # Обучение модели
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X_scaled, y)

            self.is_trained = True
            print(f"Модель успешно обучена на {len(battery_data)} записях")
            return True

        except Exception as e:
            print(f"Ошибка при обучении: {e}")
            return False

    def predict(self, battery_data: list):
        """Предсказание RUL для новых данных"""
        if not self.is_trained or self.model is None:
            print("Модель не обучена")
            return None, 0.0

        try:
            # Преобразуем всю историю батареи в DataFrame
            df = pd.DataFrame(battery_data)
            df['battery_id'] = 'current'

            features_data = self.prepare_features(df)

            if not features_data:
                print("Не удалось подготовить признаки для предсказания")
                return None, 0.0

            X = [features_data[0][0]]
            X_scaled = self.scaler.transform(X)

            prediction = self.model.predict(X_scaled)[0]

            # Confidence на основе близости к обучающим данным
            confidence = min(0.95, max(0.1, 1.0 - abs(prediction - 500) / 1000))

            return max(0, prediction), confidence

        except Exception as e:
            print(f"Ошибка при предсказании: {e}")
            return None, 0.0

    def save_model(self, filepath):
        """Сохранение модели"""
        if self.is_trained:
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }, filepath)
            print(f"Модель сохранена в {filepath}")

    def load_model(self, filepath):
        """Загрузка модели"""
        if os.path.exists(filepath):
            loaded = joblib.dump(filepath)
            self.model = loaded['model']
            self.scaler = loaded['scaler']
            self.is_trained = loaded['is_trained']
            print(f"Модель загружена из {filepath}")
        else:
            print(f"Файл {filepath} не найден")