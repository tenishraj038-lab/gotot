import pytest
from unittest.mock import patch, MagicMock


class TestSettings:
    def test_settings_load(self):
        with patch.dict("os.environ", {"SECRET_KEY": "test-key"}):
            from app.config import Settings
            s = Settings(secret_key="test-key")
            assert s.secret_key == "test-key"
            assert s.environment == "development"
            assert s.download_dir == "/tmp/downloads"

    def test_settings_defaults(self):
        with patch.dict("os.environ", {"SECRET_KEY": "test"}):
            from app.config import Settings
            s = Settings(secret_key="test")
            assert s.currency == "USD"
            assert s.algorithm == "HS256"
            assert s.access_token_expire_minutes == 60
            assert s.refresh_token_expire_days == 30
