from __future__ import annotations

import pytest

from endpoints.account_endpoint import AccountEndpoint
from endpoints.contact_endpoint import ContactEndpoint
from endpoints.opportunity_endpoint import OpportunityEndpoint
from endpoints.quote_endpoint import QuoteEndpoint
from endpoints.order_endpoint import OrderEndpoint
from endpoints.contract_endpoint import ContractEndpoint
from pages.qle_page import QLEPage
from utils.excel_reader import ExcelReader
from utils.excel_writer import ExcelWriter
from workflows.cpq_workflow import CPQWorkflow


@pytest.fixture
def cpq_workflow(
    account_endpoint: AccountEndpoint,
    contact_endpoint: ContactEndpoint,
    opportunity_endpoint: OpportunityEndpoint,
    quote_endpoint: QuoteEndpoint,
    order_endpoint: OrderEndpoint,
    contract_endpoint: ContractEndpoint,
    qle_page: QLEPage,
    excel_reader: ExcelReader,
    excel_writer: ExcelWriter,
) -> CPQWorkflow:
    return CPQWorkflow(
        account_endpoint=account_endpoint,
        contact_endpoint=contact_endpoint,
        opportunity_endpoint=opportunity_endpoint,
        quote_endpoint=quote_endpoint,
        order_endpoint=order_endpoint,
        contract_endpoint=contract_endpoint,
        qle_page=qle_page,
        excel_reader=excel_reader,
        excel_writer=excel_writer,
    )
