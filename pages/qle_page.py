from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from config.settings import settings
from pages.base_page import BasePage
from utils.log_context import set_action, set_data, set_method, set_object
from utils.system_logger import get_logger
from utils.shadow_dom import DEEP_FIND_JS

from components.pricebook_dialog import PricebookDialogComponent

logger = get_logger(__name__)

QLE_IFRAME = 'iframe[name^="vfFrameId_"][height="100%"]'


class QLEPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.pricebook_dialog = PricebookDialogComponent(page)

    def _qle_frame(self):
        return self.page.frame_locator(QLE_IFRAME)

    def _sb_frame(self):
        return next((f for f in self.page.frames if "/apex/sb?" in (f.url or "")), None)

    def open_quote_record(self, quote_id: str) -> None:
        """Navigates to the Quote record page view."""
        self.open_record("SBQQ__Quote__c", quote_id)

    def click_edit_lines(self) -> None:
        set_object("QLEPage")
        set_method("click_edit_lines")
        set_action("CLICK_EDIT_LINES")
        logger.info("STATUS=START")
        edit_lines = self.page.locator('button.slds-button:has-text("Edit Lines")')
        edit_lines.wait_for(timeout=20_000)
        edit_lines.click()
        self.page.wait_for_selector(QLE_IFRAME, timeout=30_000)
        logger.info("STATUS=PASS")

    def force_close_pricebook_popup(self) -> None:
        """Delegates to reusable PricebookDialogComponent."""
        self.pricebook_dialog.dismiss_if_visible()

    def handle_pricebook_dialog(self) -> None:
        """Checks and dismisses the pricebook dialog if present, then waits for Add Products button."""
        set_object("QLEPage")
        set_method("handle_pricebook_dialog")
        set_action("HANDLE_PRICEBOOK_DIALOG")
        logger.info("STATUS=START")
        frame = self._qle_frame()
        self.pricebook_dialog.dismiss_if_visible()
        frame.get_by_role("button", name="Add Products").wait_for(timeout=60_000)
        logger.info("STATUS=PASS")

    def click_add_products(self, product_code: str) -> None:
        set_object("QLEPage")
        set_method("click_add_products")
        set_action("CLICK_ADD_PRODUCTS")
        set_data(f"product_code={product_code}")
        logger.info("STATUS=START")
        frame = self._qle_frame()
        frame.get_by_role("button", name="Add Products").click()
        frame.locator(f'span#me:has-text("{product_code}")').wait_for(timeout=30_000)
        logger.info("STATUS=PASS")

    def select_product(self, product_code: str) -> None:
        set_object("QLEPage")
        set_method("select_product")
        set_action("SELECT_PRODUCT")
        set_data(f"product_code={product_code}")
        logger.info("STATUS=START")
        frame = self._qle_frame()
        product_checkbox = (
            frame.locator("sb-swipe-container")
            .filter(has=frame.locator(f'span#me:has-text("{product_code}")'))
            .get_by_role("checkbox")
        )
        product_checkbox.wait_for(timeout=20_000)
        product_checkbox.click()
        frame.locator("paper-button#plSelect").click()
        frame.locator(f'span#me:has-text("{product_code}")').first.wait_for(timeout=30_000)
        logger.info("STATUS=PASS")

    def click_calculate(self) -> None:
        set_object("QLEPage")
        set_method("click_calculate")
        set_action("CALCULATE")
        logger.info("STATUS=START")
        calc_btn = self._qle_frame().get_by_role("button", name="Calculate")
        calc_btn.wait_for(timeout=30_000)
        calc_btn.click(force=True)
        self.page.wait_for_timeout(5000)
        logger.info("STATUS=PASS")

    def save_quote_lines(self) -> None:
        set_object("QLEPage")
        set_method("save_quote_lines")
        set_action("SAVE_QUOTE_LINES")
        logger.info("STATUS=START")
        save_btn = self._qle_frame().get_by_role("button", name="Save", exact=True)
        save_btn.wait_for(timeout=30_000)
        save_btn.click(force=True)
        self.page.wait_for_url("**/lightning/r/SBQQ__Quote__c/**", timeout=60_000)
        self.page.wait_for_timeout(5000)
        expect(self.page).to_have_url(re.compile(r".*/lightning/r/SBQQ__Quote__c/.*"))
        logger.info("STATUS=PASS")
