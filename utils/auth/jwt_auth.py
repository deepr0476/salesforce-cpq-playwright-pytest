from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import httpx

from config.settings import settings
from utils.log_context import set_action, set_method, set_object
from utils.system_logger import get_logger

logger = get_logger(__name__)


@dataclass
class SalesforceAuth:
    access_token: str
    instance_url: str


class JwtAuth:
    def __init__(self, private_key_path: Path | None = None):
        set_object("JwtAuth")
        self._private_key_path = private_key_path or settings.private_key_path
        self._cached: SalesforceAuth | None = None
        self._token_expiry: datetime | None = None

    def get_access_token(self) -> SalesforceAuth:
        set_object("JwtAuth")
        set_method("get_access_token")
        set_action("GET_ACCESS_TOKEN")
        if self._cached and self._token_expiry and datetime.now() < self._token_expiry:
            logger.info("STATUS=PASS AUTHENTICATION=JWT CACHE=HIT")
            return self._cached

        logger.info("STATUS=START AUTHENTICATION=JWT")
        missing = []
        if not settings.sf_client_id:
            missing.append("SF_CLIENT_ID")
        if not settings.sf_username:
            missing.append("SF_USERNAME")
        if not settings.sf_login_url:
            missing.append("SF_LOGIN_URL")
        if not self._private_key_path.exists():
            raise FileNotFoundError(f"PRIVATE_KEY_PATH not found: {self._private_key_path}")
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")

        private_key = self._private_key_path.read_text(encoding="utf-8")
        assertion = jwt.encode(
            {
                "iss": settings.sf_client_id,
                "sub": settings.sf_username,
                "aud": settings.sf_login_url,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=3),
            },
            private_key,
            algorithm="RS256",
        )

        url = f"{settings.sf_login_url}/services/oauth2/token"
        try:
            response = httpx.post(
                url,
                params={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            body = response.json()
        except Exception:
            logger.exception("STATUS=FAIL AUTHENTICATION=JWT")
            raise

        access_token = body.get("access_token")
        instance_url = body.get("instance_url")
        if not access_token or not instance_url:
            raise RuntimeError("JWT token response missing access_token or instance_url")

        self._cached = SalesforceAuth(access_token=access_token, instance_url=instance_url)
        self._token_expiry = datetime.now() + timedelta(minutes=2)
        logger.info("STATUS=PASS AUTHENTICATION=JWT")
        return self._cached
