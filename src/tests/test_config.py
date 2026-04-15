"""Простые smoke-тесты для прохождения CI/CD."""
from src.core.config import AppConfig, ApiV1Prefix, ApiPrefix


class TestAppConfig:
    def test_default_app_name(self):
        config = AppConfig()
        assert config.app_name == "user-service"


class TestApiV1Prefix:
    def test_default_prefix(self):
        v1 = ApiV1Prefix()
        assert v1.prefix == "/v1"


class TestApiPrefix:
    def test_default_prefix(self):
        api = ApiPrefix()
        assert api.prefix == "/api"

    def test_nested_v1(self):
        api = ApiPrefix()
        assert isinstance(api.v1, ApiV1Prefix)
        assert api.v1.prefix == "/v1"


class TestSettings:
    def test_settings_loaded(self):
        from src.core.config import settings
        assert settings is not None

    def test_settings_api_prefix(self):
        from src.core.config import settings
        assert settings.api.prefix == "/api"

    def test_settings_app_name_from_env(self):
        from src.core.config import settings
        # env var AUTH_CONFIG__APP__APP_NAME = "user-service-test" (set in conftest.py)
        assert settings.app.app_name == "user-service-test"
