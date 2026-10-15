from __future__ import annotations

import time

from endpoints.api_client import ApiClient
from config.settings import settings
from utils.log_context import set_action, set_data, set_method, set_object
from utils.system_logger import get_logger

logger = get_logger(__name__)


class ContractEndpoint:
    def __init__(self, client: ApiClient):
        self.client = client

    def create_contract_from_order(self, order_id: str) -> str | None:
        set_object("ContractEndpoint")
        set_method("create_contract_from_order")
        set_action("CREATE_CONTRACT_FROM_ORDER")
        set_data(f"order_id={order_id}")
        logger.info("STATUS=START")
        self.client.api_request(
            "patch",
            f"sobjects/Order/{order_id}",
            {"SBQQ__Contracted__c": True},
        )
        last_result = None
        for attempt in range(1, settings.contract_query_retries + 1):
            time.sleep(settings.contract_query_wait_ms / 1000)
            last_result = self.client.api_request(
                "get",
                f"query?q=SELECT+Id,ContractNumber+FROM+Contract+WHERE+SBQQ__Order__c='{order_id}'+LIMIT+1",
            )
            records = (last_result or {}).get("records") or []
            if records:
                contract_id = records[0]["Id"]
                logger.info(
                    "STATUS=PASS RECORD_ID=%s CONTRACT_NUMBER=%s ATTEMPT=%s",
                    contract_id,
                    records[0].get("ContractNumber"),
                    attempt,
                )
                return contract_id
            logger.info("STATUS=WAIT ATTEMPT=%s/%s", attempt, settings.contract_query_retries)
        logger.info("STATUS=PASS CONTRACT=NOT_GENERATED_YET")
        return None
