from __future__ import annotations

import time

from endpoints.api_client import ApiClient
from config.settings import settings
from utils.log_context import set_action, set_data, set_method, set_object
from utils.system_logger import get_logger

logger = get_logger(__name__)


class OrderEndpoint:
    def __init__(self, client: ApiClient):
        self.client = client

    def create_order_from_quote(self, quote_id: str) -> str:
        set_object("OrderEndpoint")
        set_method("create_order_from_quote")
        set_action("CREATE_ORDER_FROM_QUOTE")
        set_data(f"quote_id={quote_id}")
        logger.info("STATUS=START")
        self.client.api_request(
            "patch",
            f"sobjects/SBQQ__Quote__c/{quote_id}",
            {"SBQQ__Ordered__c": True},
        )
        last_result = None
        for attempt in range(1, settings.order_query_retries + 1):
            time.sleep(settings.order_query_wait_ms / 1000)
            last_result = self.client.api_request(
                "get",
                f"query?q=SELECT+Id,OrderNumber+FROM+Order+WHERE+SBQQ__Quote__c='{quote_id}'+LIMIT+1",
            )
            records = (last_result or {}).get("records") or []
            if records:
                order_id = records[0]["Id"]
                logger.info(
                    "STATUS=PASS RECORD_ID=%s ORDER_NUMBER=%s ATTEMPT=%s",
                    order_id,
                    records[0].get("OrderNumber"),
                    attempt,
                )
                return order_id
            logger.info("STATUS=WAIT ATTEMPT=%s/%s", attempt, settings.order_query_retries)
        raise RuntimeError("Order not found after retries")

    def activate_order(self, order_id: str) -> None:
        set_object("OrderEndpoint")
        set_method("activate_order")
        set_action("ACTIVATE_ORDER")
        set_data(f"order_id={order_id}")
        logger.info("STATUS=START")
        self.client.api_request(
            "patch",
            f"sobjects/Order/{order_id}",
            {"Status": "Activated"},
        )
        logger.info("STATUS=PASS")
