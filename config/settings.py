from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SUPPORTED_ENVIRONMENTS = {"QA", "DEV", "UAT"}

# 1. First, load the default root .env (which can specify default ENV=QA)
load_dotenv(PROJECT_ROOT / ".env", override=False)

# 2. Resolve environment name (CLI OS env takes top precedence over root .env)
target_env = os.getenv("ENV", "QA").strip().upper()

# 3. Fail-Fast Validation: Strict rejection of unsupported environments like P2
if target_env not in SUPPORTED_ENVIRONMENTS:
    raise ValueError(
        f"CRITICAL CONFIGURATION ERROR: Invalid environment '{target_env}'. "
        f"Supported environments are: {sorted(SUPPORTED_ENVIRONMENTS)}"
    )

# 4. Load the dedicated environment file (e.g. .env.qa, .env.dev, .env.uat)
env_file = PROJECT_ROOT / f".env.{target_env.lower()}"
if not env_file.exists():
    raise FileNotFoundError(
        f"CRITICAL CONFIGURATION ERROR: Configuration file '{env_file.name}' not found for ENV='{target_env}'."
    )

load_dotenv(env_file, override=True)


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


@dataclass(frozen=True)
class Settings:
    environment: str
    sf_client_id: str
    sf_username: str
    sf_login_url: str
    private_key_path: Path
    salesforce_instance: str
    sf_instance_url: str
    sf_api_version: str
    test_timeout_ms: int
    expect_timeout_ms: int
    action_timeout_ms: int
    navigation_timeout_ms: int
    headless: bool
    slow_mo_ms: int
    viewport_width: int
    viewport_height: int
    video_width: int
    video_height: int
    locale: str
    timezone_id: str
    geolocation_latitude: float
    geolocation_longitude: float
    video_mode: str
    excel_path: Path
    order_query_retries: int
    order_query_wait_ms: int
    contract_query_retries: int
    contract_query_wait_ms: int


def load_settings() -> Settings:
    key_path = Path(os.getenv("PRIVATE_KEY_PATH", "./server.key"))
    if not key_path.is_absolute():
        key_path = PROJECT_ROOT / key_path

    return Settings(
        environment=target_env,
        sf_client_id=os.getenv("SF_CLIENT_ID", ""),
        sf_username=os.getenv("SF_USERNAME", ""),
        sf_login_url=os.getenv("SF_LOGIN_URL", "https://login.salesforce.com").rstrip("/"),
        private_key_path=key_path,
        salesforce_instance=os.getenv("SALESFORCE_INSTANCE", "").rstrip("/"),
        sf_instance_url=os.getenv("SF_INSTANCE_URL", "").rstrip("/"),
        sf_api_version=os.getenv("SF_API_VERSION", "v57.0"),
        test_timeout_ms=_int("TEST_TIMEOUT_MS", 300_000),
        expect_timeout_ms=_int("EXPECT_TIMEOUT_MS", 30_000),
        action_timeout_ms=_int("ACTION_TIMEOUT_MS", 30_000),
        navigation_timeout_ms=_int("NAVIGATION_TIMEOUT_MS", 30_000),
        headless=_bool("HEADLESS", False),
        slow_mo_ms=_int("SLOW_MO", 800),
        viewport_width=1600,
        viewport_height=900,
        video_width=1920,
        video_height=1080,
        locale="en-IN",
        timezone_id="Asia/Kolkata",
        geolocation_latitude=28.6139,
        geolocation_longitude=77.2090,
        video_mode=os.getenv("VIDEO_MODE", "on"),
        excel_path=PROJECT_ROOT / "test_data" / "test_data.xlsx",
        order_query_retries=_int("ORDER_QUERY_RETRIES", 10),
        order_query_wait_ms=_int("ORDER_QUERY_WAIT_MS", 3000),
        contract_query_retries=_int("CONTRACT_QUERY_RETRIES", 6),
        contract_query_wait_ms=_int("CONTRACT_QUERY_WAIT_MS", 5000),
    )


settings = load_settings()
