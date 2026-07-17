import logging
import json
from datetime import datetime, timezone
from typing import Optional
from app.config import get_settings

logger = logging.getLogger("gotot.audit")


class AuditLogger:
    def __init__(self):
        self.settings = get_settings()

    def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[dict] = None,
        status: str = "success",
    ):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user_id": user_id,
            "email": email,
            "ip_address": ip_address,
            "resource": resource,
            "details": details or {},
            "status": status,
            "environment": self.settings.environment,
        }
        logger.info(f"AUDIT: {json.dumps(entry)}")

        try:
            from app.models.database import async_session
            from app.models.audit import AuditLog

            async def _save():
                try:
                    async with async_session() as session:
                        session.add(AuditLog(
                            action=action,
                            user_id=user_id,
                            email=email,
                            ip_address=ip_address,
                            resource=resource,
                            details=details or {},
                            status=status,
                        ))
                        await session.commit()
                except Exception:
                    pass

            import asyncio
            try:
                loop = asyncio.get_running_loop()
                if loop and loop.is_running():
                    loop.create_task(_save())
            except RuntimeError:
                pass
        except Exception:
            pass

    def login_success(self, user_id: str, email: str, ip_address: str):
        self.log("LOGIN_SUCCESS", user_id=user_id, email=email, ip_address=ip_address)

    def login_failed(self, email: str, ip_address: str):
        self.log("LOGIN_FAILED", email=email, ip_address=ip_address, status="failed")

    def register(self, user_id: str, email: str, ip_address: str):
        self.log("REGISTER", user_id=user_id, email=email, ip_address=ip_address)

    def download(self, user_id: Optional[str], url: str, platform: str, ip_address: Optional[str], status: str = "success"):
        self.log("DOWNLOAD", user_id=user_id, ip_address=ip_address, resource=url, details={"platform": platform}, status=status)

    def admin_action(self, admin_id: str, action: str, resource: str, details: Optional[dict] = None):
        self.log(f"ADMIN_{action.upper()}", user_id=admin_id, resource=resource, details=details)

    def payment(self, user_id: str, amount: float, payment_type: str, status: str = "completed"):
        self.log("PAYMENT", user_id=user_id, details={"amount": amount, "payment_type": payment_type}, status=status)


audit_logger = AuditLogger()
