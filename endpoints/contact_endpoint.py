from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from faker import Faker

from endpoints.api_client import ApiClient
from utils.log_context import set_action, set_data, set_method, set_object
from utils.system_logger import get_logger

logger = get_logger(__name__)
fake = Faker()


class ContactEndpoint:
    def __init__(self, client: ApiClient):
        self.client = client
        self.last_created_name: str = ""
        self.last_created_payload: dict[str, Any] = {}

    def create_contact(self, account_id: str, data: dict[str, Any] | None = None) -> str:
        set_object("ContactEndpoint")
        set_method("create_contact")
        set_action("CREATE_CONTACT")
        set_data(f"account_id={account_id}")
        if not account_id:
            raise ValueError("account_id required")
        logger.info("STATUS=START")
        data = data or {}
        if not isinstance(data, dict):
            data = {}

        account = self.client.api_request(
            "get",
            f"sobjects/Account/{account_id}?fields=BillingStreet,BillingCity,BillingState,BillingPostalCode,BillingCountry,Phone",
        )
        unique = datetime.now().strftime("%Y%m%d%H%M%S")
        last_name = data.get("last_name") or fake.last_name()
        full_last_name = f"{last_name}_{unique}"
        self.last_created_name = full_last_name
        email = data.get("email") or fake.email()
        contact_data = {
            "Salutation": data.get("salutation", "Mr."),
            "LastName": full_last_name,
            "Email": email,
            "Phone": account.get("Phone"),
            "MailingStreet": account.get("BillingStreet"),
            "MailingCity": account.get("BillingCity"),
            "MailingState": account.get("BillingState"),
            "MailingPostalCode": account.get("BillingPostalCode"),
            "MailingCountry": account.get("BillingCountry"),
            "AccountId": account_id,
        }
        self.last_created_payload = contact_data
        result = self.client.api_request("post", "sobjects/Contact", contact_data)
        contact_id = result.get("id") if isinstance(result, dict) else None
        if not contact_id or not re.match(r"^[a-zA-Z0-9]{15}([a-zA-Z0-9]{3})?$", contact_id):
            err_msg = f"Invalid Salesforce ID returned from Contact API: {contact_id} (Result: {result})"
            logger.error(f"CRITICAL API ASSERTION FAILED: {err_msg}")
            raise ValueError(err_msg)
        logger.info("STATUS=PASS RECORD_ID=%s", contact_id)
        return contact_id

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        return self.client.api_request(
            "get",
            f"sobjects/Contact/{contact_id}?fields=Id,AccountId,LastName,Email,Phone",
        )
