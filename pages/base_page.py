from __future__ import annotations

import re
from playwright.sync_api import Page, expect

from config.settings import settings
from utils.log_context import set_action, set_data, set_method, set_object
from utils.system_logger import get_logger

logger = get_logger(__name__)


class BasePage:
    """Base class for all Salesforce UI Page Objects."""

    def __init__(self, page: Page):
        self.page = page

    def open_record(self, sobject_api_name: str, record_id: str) -> None:
        """Navigates directly to any standard or custom Salesforce record view."""
        set_object("BasePage")
        set_method("open_record")
        set_action(f"OPEN_{sobject_api_name.upper()}_RECORD")
        set_data(f"sobject={sobject_api_name} record_id={record_id}")
        logger.info("STATUS=START")
        url = f"{settings.sf_instance_url}/lightning/r/{sobject_api_name}/{record_id}/view"
        self.page.goto(url)
        self.page.wait_for_url(f"**/lightning/r/{sobject_api_name}/**", timeout=30_000)
        logger.info("STATUS=PASS")

    def wait_for_lightning_ready(self, timeout_ms: int = 15_000) -> None:
        """Waits for standard Salesforce Lightning container to be fully visible."""
        expect(self.page).to_have_url(re.compile(r".*lightning.*"), timeout=timeout_ms)
