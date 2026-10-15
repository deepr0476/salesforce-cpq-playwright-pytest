from __future__ import annotations

import re
import pytest
from playwright.sync_api import Page, expect

from config.settings import PROJECT_ROOT, settings
from pages.qle_page import QLEPage
from utils.auth.jwt_auth import JwtAuth
from utils.log_context import set_action, set_object
from utils.system_logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def authenticated_page(page: Page, jwt_auth: JwtAuth) -> Page:
    set_object("JwtAuth")
    auth_dir = PROJECT_ROOT / ".auth"
    auth_dir.mkdir(parents=True, exist_ok=True)
    storage_file = auth_dir / f"storage_state_{settings.environment.lower()}.json"

    # 1. Fast-Path: Storage State Reuse (~1s login)
    if storage_file.exists():
        logger.info("STATUS=START AUTHENTICATION=STORAGE_STATE_REUSE")
        try:
            # Inject storage_state cookies directly into page context if not loaded automatically
            import json
            with open(storage_file, "r") as f:
                state_data = json.load(f)
            cookies = state_data.get("cookies", [])
            if cookies:
                page.context.add_cookies(cookies)

            home_url = f"{settings.sf_instance_url}/lightning/page/home"
            page.goto(home_url, wait_until="load", timeout=settings.navigation_timeout_ms)
            page.wait_for_url("**/lightning/**", timeout=settings.navigation_timeout_ms)
            # Ensure not redirected to login
            if "login.salesforce.com" in page.url or "/secur/login" in page.url:
                raise RuntimeError(f"Session expired, redirected to login: {page.url}")
            expect(page.get_by_role("heading", name="Home")).to_be_visible(timeout=settings.expect_timeout_ms)
            logger.info("STATUS=PASS AUTHENTICATION=STORAGE_STATE_REUSE")
            return page
        except Exception as exc:
            logger.warning("STATUS=RETRY AUTHENTICATION=STORAGE_STATE_EXPIRED ERROR=%s CURRENT_URL=%s", exc, page.url)

    # 2. JWT Frontdoor Login Flow
    set_action("FRONTDOOR_LOGIN")
    logger.info("STATUS=START AUTHENTICATION=JWT_FRONTDOOR")
    token = jwt_auth.get_access_token().access_token
    frontdoor = (
        f"{settings.salesforce_instance}/secur/frontdoor.jsp"
        f"?sid={token}&retURL=/lightning/page/home"
    )
    page.goto(frontdoor, wait_until="load")
    page.wait_for_url("**/lightning/**", timeout=30_000)
    expect(page.get_by_role("heading", name="Home")).to_be_visible(timeout=15000)
    expect(page).to_have_url(re.compile(r".*lightning.*"))

    # 3. Cache Authenticated State to Storage State
    try:
        page.context.storage_state(path=str(storage_file))
        logger.info("STATUS=SAVED_STORAGE_STATE PATH=%s", storage_file)
    except Exception as exc:
        logger.warning("STATUS=WARN FAILED_SAVING_STORAGE_STATE ERROR=%s", exc)

    logger.info("STATUS=PASS AUTHENTICATION=JWT_FRONTDOOR")
    return page


@pytest.fixture
def qle_page(authenticated_page: Page) -> QLEPage:
    return QLEPage(authenticated_page)
