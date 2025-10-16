from __future__ import annotations

import logging
import random
import smtplib
import ssl
import threading
import time
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Dict, Optional

from core.config import get_settings

_logger = logging.getLogger(__name__)


class EmailNotConfiguredError(RuntimeError):
    """Raised when SMTP credentials are missing."""


class EmailDispatchError(RuntimeError):
    """Raised when an OTP email cannot be delivered."""


@dataclass
class _OtpRecord:
    code: str
    expires_at: float


class OtpService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._store: Dict[str, _OtpRecord] = {}
        self._lock = threading.Lock()
        self._rng = random.SystemRandom()

    def send_code(self, email: str) -> None:
        email_key = self._normalise_email(email)
        code = self._generate_code()
        expires_at = time.monotonic() + self._settings.otp_expiry_seconds
        with self._lock:
            self._store[email_key] = _OtpRecord(code=code, expires_at=expires_at)
        try:
            self._dispatch(email, code)
        except Exception:
            with self._lock:
                self._store.pop(email_key, None)
            raise

    def verify_code(self, email: str, code: str) -> bool:
        email_key = self._normalise_email(email)
        now = time.monotonic()
        with self._lock:
            record = self._store.get(email_key)
            if not record:
                return False
            if now > record.expires_at:
                self._store.pop(email_key, None)
                return False
            if record.code != code.strip():
                return False
            self._store.pop(email_key, None)
            return True

    def active_count(self) -> int:
        self._prune_expired()
        with self._lock:
            return len(self._store)

    def _generate_code(self) -> str:
        return f"{self._rng.randrange(0, 10**6):06d}"

    def _normalise_email(self, email: str) -> str:
        return email.strip().lower()

    def _prune_expired(self) -> None:
        now = time.monotonic()
        with self._lock:
            expired = [key for key, record in self._store.items() if now > record.expires_at]
            for key in expired:
                self._store.pop(key, None)

    def _dispatch(self, email: str, code: str) -> None:
        transport = self._settings.email_transport
        if transport == "console":
            _logger.info("OTP for %s: %s", email, code)
            return
        if transport != "smtp":
            raise EmailDispatchError(f"Unsupported email transport: {transport}")
        if not self._settings.email_user or not self._settings.email_password:
            raise EmailNotConfiguredError("Email credentials are not configured.")
        try:
            self._send_via_smtp(email, code)
        except EmailDispatchError:
            raise
        except EmailNotConfiguredError:
            raise
        except Exception as exc:
            raise EmailDispatchError("Failed to send OTP email.") from exc

    def _send_via_smtp(self, email: str, code: str) -> None:
        settings = self._settings
        sender = settings.email_user
        if settings.email_from_name:
            sender = f"{settings.email_from_name} <{settings.email_user}>"

        message = EmailMessage()
        message["From"] = sender
        message["To"] = email
        message["Subject"] = "Your DataCue verification code"
        plain_text = (
            f"Use this code to finish signing in: {code}\n\n"
            f"This code expires in {max(1, settings.otp_expiry_seconds // 60)} minutes."
        )
        message.set_content(plain_text)
        message.add_alternative(
            (
                "<p>Use this code to finish signing in:</p>"
                f"<p style=\"font-size: 1.5rem; font-weight: bold; letter-spacing: 0.3rem;\">{code}</p>"
                f"<p>This code expires in {max(1, settings.otp_expiry_seconds // 60)} minutes.</p>"
            ),
            subtype="html",
        )

        context = ssl.create_default_context()
        if settings.email_use_ssl:
            with smtplib.SMTP_SSL(settings.email_smtp_host, settings.email_smtp_port, context=context) as server:
                server.login(settings.email_user, settings.email_password)
                server.send_message(message)
            return

        with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port) as server:
            server.ehlo()
            if settings.email_use_tls:
                server.starttls(context=context)
                server.ehlo()
            server.login(settings.email_user, settings.email_password)
            server.send_message(message)


_service: Optional[OtpService] = None
_service_lock = threading.Lock()


def get_otp_service() -> OtpService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _logger.debug("Creating OtpService instance")
                _service = OtpService()
    return _service


def reset_otp_service() -> None:
    global _service
    with _service_lock:
        _service = None
*** End File