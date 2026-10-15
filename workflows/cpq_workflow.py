from __future__ import annotations

import allure
from playwright.sync_api import expect
import time
from dataclasses import dataclass, field
from typing import Any

from endpoints.account_endpoint import AccountEndpoint
from endpoints.contact_endpoint import ContactEndpoint
from endpoints.opportunity_endpoint import OpportunityEndpoint
from endpoints.quote_endpoint import QuoteEndpoint
from endpoints.order_endpoint import OrderEndpoint
from endpoints.contract_endpoint import ContractEndpoint
from pages.qle_page import QLEPage
from utils.excel_reader import ExcelReader
from utils.excel_writer import ExcelWriter, now_ts
from utils.log_context import set_step
from utils.system_logger import get_logger

logger = get_logger(__name__)


@dataclass
class CPQContext:
    """Carries business data and runtime IDs across workflow steps."""
    # Data from Excel
    product_code: str = ""
    quantity: int = 1
    pricebook_name: str = ""
    discount: float = 0.0
    expected_status: str = "Draft"
    quote_data: dict[str, Any] = field(default_factory=dict)
    
    # Generated Salesforce entity identifiers and names
    account_id: str = ""
    account_name: str = ""
    contact_id: str = ""
    contact_name: str = ""
    opportunity_id: str = ""
    quote_id: str = ""
    order_id: str = ""
    contract_id: str = ""


class CPQWorkflow:
    """
    Reusable Business Workflow orchestrating API backend staging,
    UI Quote Line Editor interactions, and post-quote lifecycle.
    """

    def __init__(
        self,
        account_endpoint: AccountEndpoint,
        contact_endpoint: ContactEndpoint,
        opportunity_endpoint: OpportunityEndpoint,
        quote_endpoint: QuoteEndpoint,
        order_endpoint: OrderEndpoint,
        contract_endpoint: ContractEndpoint,
        qle_page: QLEPage,
        excel_reader: ExcelReader,
        excel_writer: ExcelWriter,
    ):
        self.account_ep = account_endpoint
        self.contact_ep = contact_endpoint
        self.opp_ep = opportunity_endpoint
        self.quote_ep = quote_endpoint
        self.order_ep = order_endpoint
        self.contract_ep = contract_endpoint
        self.qle_page = qle_page
        self.excel_reader = excel_reader
        self.excel_writer = excel_writer

    def load_scenario_data(self) -> CPQContext:
        """Reads test parameters dynamically from the Excel Single Source of Truth."""
        quote_data = self.excel_reader.get_first_row("quotes")
        product_data = self.excel_reader.get_first_row("products")
        discount_data = self.excel_reader.get_first_row("discounts")
        pricebook_data = self.excel_reader.get_first_row("pricebooks")

        ctx = CPQContext(
            product_code=str(product_data["product_code"]),
            quantity=int(product_data["quantity"]),
            pricebook_name=str(pricebook_data["pricebook_name"]),
            discount=float(discount_data["without_approval"]),
            expected_status=str(quote_data["expected_status"]),
            quote_data={
                **quote_data,
                "subscription_term": int(quote_data["subscription_term"]),
            },
        )
        return ctx

    def stage_quote_prerequisites(self, ctx: CPQContext | None = None) -> CPQContext:
        """
        Stages Account, Contact, Opportunity, and Quote via headless APIs.
        Validates Faker payloads against Salesforce records.
        """
        ctx = ctx or self.load_scenario_data()

        # 01. Create Account
        set_step("01_CREATE_ACCOUNT")
        with allure.step("01_CREATE_ACCOUNT"):
            ctx.account_id = self.account_ep.create_account()
            ctx.account_name = self.account_ep.last_created_name
            assert ctx.account_id, "Account API did not return an id"
            
            created_acc = self.account_ep.get_account(ctx.account_id)
            assert created_acc["Name"] == ctx.account_name, (
                f"Account name mismatch! Expected: {ctx.account_name}, Actual: {created_acc.get('Name')}"
            )
            logger.info("STATUS=PASS VALIDATION=ACCOUNT_PAYLOAD_MATCHED NAME=%s", ctx.account_name)

        # 02. Create Contact
        set_step("02_CREATE_CONTACT")
        with allure.step("02_CREATE_CONTACT"):
            ctx.contact_id = self.contact_ep.create_contact(ctx.account_id)
            ctx.contact_name = self.contact_ep.last_created_name
            assert ctx.contact_id, "Contact API did not return an id"

            contact_info = self.contact_ep.get_contact(ctx.contact_id)
            assert contact_info["AccountId"] == ctx.account_id, (
                f"Contact not linked to Account. expected={ctx.account_id} actual={contact_info.get('AccountId')}"
            )
            assert contact_info["LastName"] in ctx.contact_name, (
                f"Contact LastName mismatch! Expected: {ctx.contact_name}, Actual: {contact_info.get('LastName')}"
            )
            logger.info("STATUS=PASS VALIDATION=CONTACT_PAYLOAD_MATCHED NAME=%s", ctx.contact_name)

        # 03. Create Opportunity
        set_step("03_CREATE_OPPORTUNITY")
        with allure.step("03_CREATE_OPPORTUNITY"):
            ctx.opportunity_id = self.opp_ep.create_opportunity(ctx.account_id)
            assert ctx.opportunity_id, "Opportunity API did not return an id"

        # 04. Create Quote
        set_step("04_CREATE_QUOTE")
        with allure.step("04_CREATE_QUOTE"):
            ctx.quote_id = self.quote_ep.create_quote(
                ctx.opportunity_id,
                ctx.account_id,
                ctx.contact_id,
                ctx.quote_data,
            )
            assert ctx.quote_id, "Quote API did not return an id"

        # 05. Set Pricebook on Quote
        set_step("05_SET_PRICEBOOK")
        with allure.step("05_SET_PRICEBOOK"):
            self.quote_ep.set_pricebook_on_quote(ctx.quote_id, ctx.pricebook_name)

        return ctx

    def configure_quote_lines(self, ctx: CPQContext) -> None:
        """Interacts with Playwright UI to add products, calculate, and save quote lines."""
        set_step("06_OPEN_QLE_AND_ADD_PRODUCT")
        with allure.step("06_OPEN_QLE_AND_ADD_PRODUCT"):
            self.qle_page.open_quote_record(ctx.quote_id)
            self.qle_page.click_edit_lines()
            self.qle_page.handle_pricebook_dialog()
            self.qle_page.click_add_products(ctx.product_code)
            self.qle_page.select_product(ctx.product_code)
            self.qle_page.click_calculate()
            self.qle_page.save_quote_lines()

    def finalize_and_verify(self, ctx: CPQContext) -> None:
        """Sets line quantities/discounts, closes Opp, generates Order & Contract, and validates UI."""
        # 07. Set Quantity
        set_step("07_SET_QUANTITY")
        with allure.step("07_SET_QUANTITY"):
            self.quote_ep.set_quantity_on_quote_line(ctx.quote_id, ctx.quantity)

        # 08. Set Discount & Close Opp
        set_step("08_SET_DISCOUNT_AND_CLOSE_WON")
        with allure.step("08_SET_DISCOUNT_AND_CLOSE_WON"):
            self.quote_ep.set_discount_on_quote(ctx.quote_id, ctx.discount)
            self.opp_ep.close_opportunity_as_won(ctx.opportunity_id)
            opp = self.opp_ep.get_opportunity(ctx.opportunity_id)
            assert opp["StageName"] == "Closed Won", (
                f"Expected Closed Won, got {opp.get('StageName')}"
            )

        # 09. Create & Activate Order
        set_step("09_CREATE_AND_ACTIVATE_ORDER")
        with allure.step("09_CREATE_AND_ACTIVATE_ORDER"):
            ctx.order_id = self.order_ep.create_order_from_quote(ctx.quote_id)
            assert ctx.order_id, "Order was not created from quote"
            self.order_ep.activate_order(ctx.order_id)

        # 10. Create Contract
        set_step("10_CREATE_CONTRACT")
        with allure.step("10_CREATE_CONTRACT"):
            ctx.contract_id = self.contract_ep.create_contract_from_order(ctx.order_id) or ""
            assert ctx.contract_id, "Contract was not generated from order"

        # 11. Verify UI Quote Status
        set_step("11_VERIFY_QUOTE_UI_STATE")
        with allure.step("11_VERIFY_QUOTE_UI_STATE"):
            self.qle_page.open_quote_record(ctx.quote_id)
            status_locator = self.qle_page.page.locator(
                f"lightning-formatted-text:has-text('{ctx.expected_status}')"
            )
            expect(status_locator).to_be_visible(timeout=10000)

    def write_execution_summary(
        self,
        test_case_name: str,
        status: str,
        ctx: CPQContext,
        error_message: str,
        duration_seconds: float,
    ) -> None:
        """Writes execution telemetry and generated names/IDs back to Excel."""
        self.excel_writer.write_result(
            "execution_results",
            {
                "test_case": test_case_name,
                "status": status,
                "account_name": ctx.account_name,
                "account_id": ctx.account_id,
                "contact_name": ctx.contact_name,
                "contact_id": ctx.contact_id,
                "opportunity_id": ctx.opportunity_id,
                "quote_id": ctx.quote_id,
                "order_id": ctx.order_id,
                "contract_id": ctx.contract_id,
                "error_message": error_message,
                "execution_timestamp": now_ts(),
                "duration_seconds": duration_seconds,
            },
        )
