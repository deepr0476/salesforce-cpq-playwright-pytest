from __future__ import annotations

import pytest

from config.settings import settings
from utils.excel_reader import ExcelReader
from utils.excel_writer import ExcelWriter


@pytest.fixture(scope="session")
def excel_reader() -> ExcelReader:
    return ExcelReader(settings.excel_path)


@pytest.fixture(scope="session")
def excel_writer() -> ExcelWriter:
    return ExcelWriter(settings.excel_path)
