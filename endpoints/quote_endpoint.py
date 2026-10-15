from __future__ import annotations

import calendar
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from endpoints.api_client import ApiClient
from utils.log_context import set_action, set_data, set_method, set_object
from utils.system_logger import get_logger

logger = get_logger(__name__)


def _utc_date(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d")


def _add_months(dt: datetime, months: int) -> datetime:
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


class QuoteEndpoint:
    def __init__(self, client: ApiClient):
        self.client = client

    def create_quote(
        self,
        opportunity_id: str,
        account_id: str,
        contact_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> str:
        set_object("QuoteEndpoint")
        set_method("create_quote")
        set_action("CREATE_QUOTE")
        if not opportunity_id or not account_id:
            raise ValueError("opportunity_id and account_id required")
        data = data or {}
        term = int(data.get("subscription_term", 12))
        start = datetime.now(timezone.utc)
        end = _add_months(start, term)
        set_data(f"opportunity_id={opportunity_id} account_id={account_id}")
        logger.info("STATUS=START")
        quote_data: dict[str, Any] = {
            "SBQQ__Opportunity2__c": opportunity_id,
            "SBQQ__Account__c": account_id,
            "SBQQ__Primary__c": True,
            "SBQQ__SubscriptionTerm__c": term,
            "SBQQ__StartDate__c": _utc_date(start),
            "SBQQ__EndDate__c": _utc_date(end),
        }
        if contact_id:
            quote_data["SBQQ__PrimaryContact__c"] = contact_id
        result = self.client.api_request("post", "sobjects/SBQQ__Quote__c/", quote_data)
        quote_id = result.get("id") if isinstance(result, dict) else None
        if not quote_id:
            raise RuntimeError(f"Quote create did not return id: {result}")
        logger.info("STATUS=PASS RECORD_ID=%s", quote_id)
        return quote_id

    def set_pricebook_on_quote(self, quote_id: str, pricebook_name: str) -> None:
        set_object("QuoteEndpoint")
        set_method("set_pricebook_on_quote")
        set_action("SET_PRICEBOOK")
        set_data(f"quote_id={quote_id} pricebook_name={pricebook_name}")
        logger.info("STATUS=START")
        encoded_name = quote(pricebook_name, safe="")
        soql = f"SELECT+Id+FROM+Pricebook2+WHERE+Name='{encoded_name}'+LIMIT+1"
        pb_result = self.client.api_request("get", f"query?q={soql}")
        records = (pb_result or {}).get("records") or []
        if not records:
            raise RuntimeError(f"Pricebook not found: {pricebook_name}")
        pricebook_id = records[0]["Id"]
        self.client.api_request(
            "patch",
            f"sobjects/SBQQ__Quote__c/{quote_id}",
            {"SBQQ__PricebookId__c": pricebook_id},
        )
        logger.info("STATUS=PASS PRICEBOOK_ID=%s", pricebook_id)

    def set_discount_on_quote(self, quote_id: str, discount_percent: float) -> None:
        set_object("QuoteEndpoint")
        set_method("set_discount_on_quote")
        set_action("SET_DISCOUNT")
        set_data(f"quote_id={quote_id} discount_percent={discount_percent}")
        logger.info("STATUS=START")
        self.client.api_request(
            "patch",
            f"sobjects/SBQQ__Quote__c/{quote_id}",
            {"SBQQ__CustomerDiscount__c": discount_percent},
        )
        logger.info("STATUS=PASS")

    def set_quantity_on_quote_line(self, quote_id: str, quantity: int) -> None:
        set_object("QuoteEndpoint")
        set_method("set_quantity_on_quote_line")
        set_action("SET_QUANTITY")
        set_data(f"quote_id={quote_id} quantity={quantity}")
        if quantity <= 1:
            logger.info("STATUS=PASS SKIPPED reason=quantity_lte_1")
            return
        logger.info("STATUS=START")
        result = self.client.api_request(
            "get",
            f"query?q=SELECT+Id+FROM+SBQQ__QuoteLine__c+WHERE+SBQQ__Quote__c='{quote_id}'+LIMIT+1",
        )
        records = (result or {}).get("records") or []
        if not records:
            raise RuntimeError("Quote Line not found")
        quote_line_id = records[0]["Id"]
        self.client.api_request(
            "patch",
            f"sobjects/SBQQ__QuoteLine__c/{quote_line_id}",
            {"SBQQ__Quantity__c": quantity},
        )
        logger.info("STATUS=PASS QUOTE_LINE_ID=%s", quote_line_id)
