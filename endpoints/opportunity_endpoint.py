from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from faker import Faker

from endpoints.api_client import ApiClient
from utils.log_context import set_action, set_data, set_method, set_object
from utils.system_logger import get_logger

logger = get_logger(__name__)
fake = Faker()


def _utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class OpportunityEndpoint:
    def __init__(self, client: ApiClient):
        self.client = client

    def create_opportunity(self, account_id: str, data: dict[str, Any] | None = None) -> str:
        set_object("OpportunityEndpoint")
        set_method("create_opportunity")
        set_action("CREATE_OPPORTUNITY")
        if not account_id:
            raise ValueError("account_id required")
        data = data or {}
        unique = datetime.now().strftime("%Y%m%d%H%M%S")
        prefix = data.get("opportunity_name_prefix") or fake.company()
        name = f"{prefix} Opportunity_{unique}"
        set_data(f"account_id={account_id} name={name}")
        logger.info("STATUS=START")
        payload = {
            "Name": name,
            "StageName": data.get("stage_name", "Prospecting"),
            "CloseDate": _utc_date(),
            "AccountId": account_id,
        }
        result = self.client.api_request("post", "sobjects/Opportunity", payload)
        opportunity_id = result.get("id") if isinstance(result, dict) else None
        if not opportunity_id or not re.match(r"^[a-zA-Z0-9]{15}([a-zA-Z0-9]{3})?$", opportunity_id):
            err_msg = f"Invalid Salesforce ID returned from Opportunity API: {opportunity_id} (Result: {result})"
            logger.error(f"CRITICAL API ASSERTION FAILED: {err_msg}")
            raise ValueError(err_msg)
        logger.info("STATUS=PASS RECORD_ID=%s", opportunity_id)
        return opportunity_id

    def close_opportunity_as_won(self, opportunity_id: str) -> None:
        set_object("OpportunityEndpoint")
        set_method("close_opportunity_as_won")
        set_action("CLOSE_OPPORTUNITY_WON")
        set_data(f"opportunity_id={opportunity_id}")
        logger.info("STATUS=START")
        self.client.api_request(
            "patch",
            f"sobjects/Opportunity/{opportunity_id}",
            {"StageName": "Closed Won", "CloseDate": _utc_date()},
        )
        logger.info("STATUS=PASS")

    def get_opportunity(self, opportunity_id: str) -> dict[str, Any]:
        return self.client.api_request(
            "get",
            f"sobjects/Opportunity/{opportunity_id}?fields=Id,StageName",
        )
