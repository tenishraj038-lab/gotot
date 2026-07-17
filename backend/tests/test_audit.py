import pytest
from app.services.audit_log import AuditLogger


class TestAuditLogger:
    def setup_method(self):
        self.logger = AuditLogger()

    def test_login_success(self, caplog):
        caplog.clear()
        with caplog.at_level("INFO"):
            self.logger.login_success("user-1", "test@test.com", "127.0.0.1")
        assert len(caplog.records) > 0
        assert "LOGIN_SUCCESS" in caplog.text
        assert "user-1" in caplog.text
        assert "test@test.com" in caplog.text

    def test_login_failed(self, caplog):
        caplog.clear()
        with caplog.at_level("INFO"):
            self.logger.login_failed("test@test.com", "127.0.0.1")
        assert "LOGIN_FAILED" in caplog.text
        assert "failed" in caplog.text

    def test_register(self, caplog):
        caplog.clear()
        with caplog.at_level("INFO"):
            self.logger.register("user-1", "test@test.com", "127.0.0.1")
        assert "REGISTER" in caplog.text

    def test_download(self, caplog):
        caplog.clear()
        with caplog.at_level("INFO"):
            self.logger.download("user-1", "https://example.com/video", "youtube", "127.0.0.1")
        assert "DOWNLOAD" in caplog.text
        assert "youtube" in caplog.text

    def test_admin_action(self, caplog):
        caplog.clear()
        with caplog.at_level("INFO"):
            self.logger.admin_action("admin-1", "toggle_ban", "user:123")
        assert "ADMIN_TOGGLE_BAN" in caplog.text
        assert "admin-1" in caplog.text

    def test_payment(self, caplog):
        caplog.clear()
        with caplog.at_level("INFO"):
            self.logger.payment("user-1", 9.99, "subscription")
        assert "PAYMENT" in caplog.text
        assert "9.99" in caplog.text
