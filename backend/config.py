from datetime import timedelta

class Settings:
    DB_USER = "root"
    DB_PASSWORD = "password"
    DB_HOST = "localhost"
    DB_PORT = "3306"
    DB_NAME = "battery_system"

    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_ME"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

settings = Settings()
