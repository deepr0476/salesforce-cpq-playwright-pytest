from __future__ import annotations

import allure
import pytest
import time

from workflows.cpq_workflow import CPQWorkflow


@pytest.mark.cpq
@pytest.mark.smoke
@allure.title("Create CPQ Quote Without Approval")
def test_user_can_create_quote_with_product_without_approval(cpq_workflow: CPQWorkflow):
    started = time.time()
    ctx = cpq_workflow.load_scenario_data()
    status = "FAILED"
    error_message =  ""

    try:
        # 1. Headless API Data Staging & Faker Assertions (Account, Contact, Opp, Quote)
        cpq_workflow.stage_quote_prerequisites(ctx)

        # 2. Quote Line Editor (QLE) UI Actions (Add Product, Calculate, Save)
        cpq_workflow.configure_quote_lines(ctx)

        # 3. Post-QLE Lifecycle & Final UI Status Verification (Order, Contract, Status)
        cpq_workflow.finalize_and_verify(ctx)

        status = "PASSED"
    except Exception as exc:
        error_message = str(exc)
        raise
    finally:
        cpq_workflow.write_execution_summary(
            test_case_name="test_user_can_create_quote_with_product_without_approval",
            status=status,
            ctx=ctx,
            error_message=error_message,
            duration_seconds=round(time.time() - started, 2),
        )
