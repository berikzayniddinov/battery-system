---

# 🔋 Battery System – RUL Prediction

Этот проект состоит из **Backend (FastAPI + SQLite)** и **Frontend (HTML, CSS, JS)** для работы с данными батарей и прогнозирования остаточного ресурса (**Remaining Useful Life, RUL**).

---

## 🚀 Запуск проекта

### 1. Клонировать репозиторий

```bash
git clone https://github.com/berikzayniddinov/battery-system.git
cd battery-system
```

---

### 2. Запуск Backend (FastAPI)

Перейдите в папку `backend`:

```bash
cd backend
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

#### ⚙️ 2.1. Загрузка датасета в базу данных

Перед первым запуском необходимо загрузить данные в базу SQLite:

```bash
py load_dataset.py
```

После выполнения вы увидите сообщение:

```
✅ Загружено 15064 записей в таблицу battery_data
```

---

#### ⚡ 2.2. Запуск сервера

```bash
uvicorn app:app --reload --port 8000
```

Backend будет доступен по адресу:
👉 [http://localhost:8000](http://localhost:8000)

Документация Swagger:
👉 [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 3. Запуск Frontend

В новом терминале перейдите в папку `frontend`:

```bash
cd frontend
```

Запустите локальный сервер:

```bash
py -m http.server 8080
```

Frontend будет доступен по адресу:
👉 [http://localhost:8080](http://localhost:8080)

---

## 📂 Структура проекта

```
battery-system/
│── backend/
│   ├── app.py                 # Основной FastAPI сервер
│   ├── load_dataset.py        # Скрипт загрузки данных в SQLite
│   ├── models.py              # SQLAlchemy модели
│   ├── database.py            # Подключение к базе данных
│   ├── battery_data.db        # Локальная база данных
│
│── frontend/
│   ├── index.html             # Главная страница
│   ├── script.js              # Логика отображения данных
│   ├── style.css              # Стили интерфейса
│
│── requirements.txt
│── README.md
```

---

## ✅ Требования

* Python **3.9+**
* Установленные зависимости из `requirements.txt`

---

## ✨ Функционал

* Сбор и хранение данных батарей (SQLite)
* API для предсказаний RUL
* Веб-интерфейс для отображения данных и графиков

---

Хочешь, я добавлю в README секцию **«🧠 Модель предсказания RUL»** с описанием, как обучается и используется модель (например, LinearRegression / RandomForest)?
