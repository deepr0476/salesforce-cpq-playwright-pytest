from __future__ import annotations

from typing import Any

import httpx

from config.settings import settings
from utils.auth.jwt_auth import JwtAuth
from utils.log_context import set_action, set_data, set_method, set_object
from utils.system_logger import get_logger

logger = get_logger(__name__)


class ApiClient:
    def __init__(self, jwt_auth: JwtAuth, api_version: str | None = None):
        self.jwt_auth = jwt_auth
        self.api_version = api_version or settings.sf_api_version
        self._http = httpx.Client(timeout=60.0)

    def api_request(self, method: str, endpoint: str, data: Any = None) -> Any:
        set_object("ApiClient")
        set_method("api_request")
        set_action(f"{method.upper()}_{endpoint.split('?')[0]}")
        set_data(f"endpoint={endpoint}")
        auth = self.jwt_auth.get_access_token()
        url = f"{auth.instance_url}/services/data/{self.api_version}/{endpoint.lstrip('/')}"
        logger.info("STATUS=START METHOD_HTTP=%s", method.upper())
        try:
            headers = {
                "Authorization": f"Bearer {auth.access_token}",
                "Content-Type": "application/json",
            }
            kwargs = {"method": method, "url": url, "headers": headers}
            if data is not None:
                kwargs["json"] = data
            response = self._http.request(**kwargs)
            if response.status_code >= 400:
                logger.error(
                    "STATUS=FAIL STATUS_CODE=%s ERROR=%s",
                    response.status_code,
                    response.text,
                )
                response.raise_for_status()
            logger.info("STATUS=PASS STATUS_CODE=%s", response.status_code)
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        except Exception:
            logger.exception("STATUS=FAIL")
            raise

    def close(self) -> None:
        self._http.close()
