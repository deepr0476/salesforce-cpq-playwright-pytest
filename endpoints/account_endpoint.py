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


class AccountEndpoint:
    def __init__(self, client: ApiClient):
        self.client = client
        self.last_created_name: str = ""
        self.last_created_payload: dict[str, Any] = {}

    def create_account(self, data: dict[str, Any] | None = None) -> str:
        set_object("AccountEndpoint")
        set_method("create_account")
        set_action("CREATE_ACCOUNT")
        data = data or {}
        unique = datetime.now().strftime("%Y%m%d%H%M%S")
        prefix = data.get("account_name_prefix") or fake.company()
        name = f"{prefix}_{unique}"
        self.last_created_name = name
        set_data(f"account_name={name}")
        logger.info("STATUS=START")
        street = data.get("billing_street") or fake.street_address()
        city = data.get("billing_city") or fake.city()
        state = data.get("billing_state") or fake.state()
        postal = str(data.get("billing_postal_code") or fake.zipcode())
        country = data.get("billing_country") or fake.country()
        phone = str(data.get("phone") or fake.phone_number())
        payload = {
            "Name": name,
            "Phone": phone,
            "BillingStreet": street,
            "BillingCity": city,
            "BillingState": state,
            "BillingPostalCode": postal,
            "BillingCountry": country,
            "ShippingStreet": street,
            "ShippingCity": city,
            "ShippingState": state,
            "ShippingPostalCode": postal,
            "ShippingCountry": country,
        }
        self.last_created_payload = payload
        result = self.client.api_request("post", "sobjects/Account", payload)
        account_id = result.get("id") if isinstance(result, dict) else None
        if not account_id or not re.match(r"^[a-zA-Z0-9]{15}([a-zA-Z0-9]{3})?$", account_id):
            err_msg = f"Invalid Salesforce ID returned from Account API: {account_id} (Result: {result})"
            logger.error(f"CRITICAL API ASSERTION FAILED: {err_msg}")
            raise ValueError(err_msg)
        logger.info("STATUS=PASS RECORD_ID=%s", account_id)
        return account_id

    def get_account(self, account_id: str) -> dict[str, Any]:
        return self.client.api_request(
            "get",
            f"sobjects/Account/{account_id}?fields=Id,Name,Phone,BillingStreet,BillingCity",
        )
