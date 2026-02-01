from database import engine, SessionLocal
from models import Base, User
from auth import hash_password

print("🗑️  Удаление старых таблиц...")
Base.metadata.drop_all(bind=engine)

print("🔨 Создание новых таблиц...")
Base.metadata.create_all(bind=engine)

print("✅ База данных успешно инициализирована!")

# Создаем тестового пользователя
db = SessionLocal()

try:
    admin_user = User(
        email="admin@example.com",
        username="admin",
        password_hash=hash_password("admin123"),
        role="ADMIN"
    )
    db.add(admin_user)

    test_user = User(
        email="test@example.com",
        username="testuser",
        password_hash=hash_password("test123"),
        role="USER"
    )
    db.add(test_user)

    db.commit()
    print("✅ Созданы тестовые пользователи:")
    print("   - admin / admin123")
    print("   - testuser / test123")
except Exception as e:
    print(f"❌ Ошибка при создании пользователей: {e}")
    db.rollback()
finally:
    db.close()