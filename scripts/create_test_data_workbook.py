"""Create test_data/test_data.xlsx for the no-approval CPQ scenario."""

from pathlib import Path

from openpyxl import Workbook

from utils.system_logger import get_logger
logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "test_data" / "test_data.xlsx"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()

    sheets: dict[str, list[list[object]]] = {
        "quotes": [
            ["subscription_term", "expected_status"],
        ],
        "products": [
            ["product_code", "quantity"],
        ],
        "discounts": [
            ["without_approval", "with_approval"],
        ],
        "pricebooks": [
            ["pricebook_name"],
        ],
        "execution_results": [
            [
                "test_case",
                "status",
                "account_name",
                "account_id",
                "contact_name",
                "contact_id",
                "opportunity_id",
                "quote_id",
                "order_id",
                "contract_id",
                "error_message",
                "execution_timestamp",
                "duration_seconds",
            ],
        ],
    }

    first = True
    for name, rows in sheets.items():
        ws = wb.active if first else wb.create_sheet(name)
        if first:
            ws.title = name
            first = False
        for row in rows:
            ws.append(row)

    wb.save(OUT)
    logger.info("STATUS=PASS ACTION=CREATE_WORKBOOK FILE=%s", OUT)


if __name__ == "__main__":
    main()
