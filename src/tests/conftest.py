import os

# Устанавливаем переменные среды ДО любого импорта из src,
# иначе Settings() упадёт — поле `app: AppConfig` обязательное.
os.environ.setdefault("USER_CONFIG__APP__APP_NAME", "user-service-test")
os.environ.setdefault("USER_CONFIG__APP__DEBUG", "true")
