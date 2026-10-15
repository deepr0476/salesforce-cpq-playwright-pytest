from __future__ import annotations

from playwright.sync_api import Page

from utils.log_context import set_action, set_method, set_object
from utils.shadow_dom import DEEP_FIND_JS
from utils.system_logger import get_logger

logger = get_logger(__name__)


class PricebookDialogComponent:
    """Encapsulates interaction with the CPQ Pricebook selection modal / dialog."""

    def __init__(self, page: Page):
        self.page = page

    def _sb_frame(self):
        return next((f for f in self.page.frames if "/apex/sb?" in (f.url or "")), None)

    def dismiss_if_visible(self) -> None:
        """Closes the pricebook dialog ONLY if rendered and visible in Shadow DOM."""
        set_object("PricebookDialogComponent")
        set_method("dismiss_if_visible")
        set_action("DISMISS_PRICEBOOK_DIALOG")
        logger.info("STATUS=START")

        sb_frame = self._sb_frame()
        if not sb_frame:
            logger.info("STATUS=PASS DETAIL=sb_frame_not_found")
            return

        result = sb_frame.evaluate(
            f"""() => {{
                {DEEP_FIND_JS}
                const dialogs = deepFindAll(document, 'sb-pricebook-dialog');
                const visibleDialog = dialogs.find(dialog => {{
                    const rect = dialog.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                }});

                if (!visibleDialog) {{
                    return 'no-visible-pricebook-dialog';
                }}

                // Only search for Save button INSIDE the visible dialog
                const buttons = deepFindAll(visibleDialog, 'paper-button, button');
                const saveBtn = buttons.find(btn => {{
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return text === 'save';
                }});

                if (!saveBtn) {{
                    return 'save-button-not-found';
                }}

                saveBtn.click();
                saveBtn.dispatchEvent(new MouseEvent('mousedown', {{ bubbles: true, composed: true, cancelable: true }}));
                saveBtn.dispatchEvent(new MouseEvent('mouseup', {{ bubbles: true, composed: true, cancelable: true }}));
                saveBtn.dispatchEvent(new MouseEvent('click', {{ bubbles: true, composed: true, cancelable: true }}));
                return 'pricebook-save-clicked';
            }}"""
        )

        if result == "pricebook-save-clicked":
            logger.info("STATUS=PASS ACTION=DISMISSED_PRICEBOOK_DIALOG RESULT=%s", result)
            self.page.wait_for_timeout(1000)
        else:
            logger.info("STATUS=PASS DETAIL=%s", result)

