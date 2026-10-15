# Salesforce CPQ Playwright + Pytest Test Automation Framework

An enterprise-grade, pure-Python test automation framework built specifically for **Salesforce CPQ (Configure, Price, Quote)**. Designed following modern modular architecture principles (inspired by industry 10-layer enterprise test architecture), combining headless API data staging with Playwright Shadow DOM UI automation.

---

## 🚀 Key Highlights & Architectural Strengths

- **Hybrid API + UI Orchestration**: Staging prerequisites (Account, Contact, Opportunity, Quote, Pricebook) via REST API in seconds, keeping browser automation focused strictly on the critical Quote Line Editor (QLE) UI.
- **Lightning-Fast Execution (~60s E2E)**: End-to-end multi-step CPQ lifecycle test runs in ~62 seconds.
- **Session Storage State Reuse (~1s Fast-Path Login)**: Uses isolated `.auth/storage_state_{env}.json` caching to bypass UI login forms on subsequent runs, with automatic graceful fallback to JWT Frontdoor authentication.
- **Polymer / Shadow DOM Handling**: Custom recursive JS traverser (`deepFindAll`) to reliably interact with Salesforce CPQ WebComponents (`sb-pricebook-dialog`, `sb-swipe-container`, `paper-button`).
- **Defensive UI Component Design**: Non-blocking modal probes (`PricebookDialogComponent`) that dismiss transient CPQ popups without brittle sleeps or unwanted clicks.
- **Strict Multi-Environment Routing (`QA`, `DEV`, `UAT`)**: Fail-fast environment validation preventing accidental execution against unsupported environments (e.g., rejecting invalid environments immediately with `ValueError`).
- **Two-Way Backend Assertions**: Validates that dynamic Faker payloads match Salesforce database records via REST API before UI execution begins.
- **Self-Cleaning Executions & Excel Tracking**: Automatically resets run results in `test_data/test_data.xlsx` and logs human-readable Account/Contact names and Salesforce Record IDs.
- **Pure-Python Native**: Zero Node.js / NPM dependencies.

---

## 🏛️ Framework Layered Architecture

```
salesforce-cpq-playwright-pytest/
├── .auth/                  # Environment-isolated browser session states (.gitignored)
├── components/             # Reusable UI component dialogs (PricebookDialogComponent, etc.)
├── config/                 # Settings & multi-env loaders (.env, .env.qa, .env.dev, .env.uat)
├── endpoints/              # Salesforce REST API endpoints (Account, Contact, Opp, Quote, Order, Contract)
├── fixtures/               # Modular pytest fixtures (api_fixtures, page_fixtures, data_fixtures, workflow_fixtures)
├── pages/                  # Page Object Models (BasePage, QLEPage)
├── test_data/              # Excel data source (test_data.xlsx) with clean execution write-backs
├── test_runs/              # Self-contained run artifacts (HTML reports, logs, videos, traces)
├── tests/                  # Declarative test suites grouped by domain (tests/cpq/)
├── utils/                  # Core utilities (JWT auth, Excel reader/writer, Shadow DOM traverser, Logger)
└── workflows/              # High-level business flows orchestrating APIs + Pages (CPQWorkflow)
```

---

## 🛠️ Prerequisites & Setup

### 1. Python Environment

Requires **Python 3.10+** (tested on Python 3.14).

```bash
# Clone the repository and navigate into project root
cd salesforce-cpq-playwright-pytest

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

### 2. Environment Configuration

The framework uses environment-specific config files (`.env.qa`, `.env.dev`, `.env.uat`):

1. Place your Salesforce Connected App RSA private key at `./server.key` (or configure path via `PRIVATE_KEY_PATH`).
2. Set default active environment in `.env`:
   ```bash
   ENV=QA
   ```
3. Populate credentials in the corresponding `.env.<env>` file (e.g. `.env.qa`):
   ```ini
   # Salesforce Connected App (JWT Bearer Flow)
   SF_CLIENT_ID=your_connected_app_consumer_key
   SF_USERNAME=your_salesforce_username
   SF_LOGIN_URL=https://login.salesforce.com
   PRIVATE_KEY_PATH=./server.key

   # Salesforce Org URLs
   SALESFORCE_INSTANCE=https://your-org.develop.my.salesforce.com
   SF_INSTANCE_URL=https://your-org.develop.lightning.force.com

   # Playwright Execution Settings
   HEADLESS=false
   SLOW_MO=800
   VIDEO_MODE=on
   ```

> [!NOTE]
> `.env`, `.env.*`, `server.key`, and `.auth/` are strictly excluded in `.gitignore` to prevent secret exposure.

---

## 🏃 Running Tests

### 1. Default Run (QA Environment)

```bash
pytest tests/cpq/test_quote_without_approval.py -s -v
```

### 2. Switching Environments via CLI

Override the environment on the fly without modifying files:

```bash
# Run against DEV
ENV=DEV pytest tests/cpq/test_quote_without_approval.py -s -v

# Run against UAT
ENV=UAT pytest tests/cpq/test_quote_without_approval.py -s -v
```

> [!IMPORTANT]
> If an unsupported environment is passed (e.g. `ENV=STAGING` or `ENV=P2`), the framework fails fast immediately:
> `ValueError: CRITICAL CONFIGURATION ERROR: Invalid environment 'STAGING'. Must be one of ['DEV', 'QA', 'UAT'].`

### 3. Targeted Test Execution with Markers

```bash
# Run CPQ Smoke tests
pytest -m "smoke and cpq" -s -v

# Run full CPQ regression suite
pytest -m cpq -v
```

---

## 📋 Declarative Test Case Example

Tests remain ultra-concise and readable (~35 lines) because low-level interactions are encapsulated inside the `CPQWorkflow`:

```python
@pytest.mark.cpq
@pytest.mark.smoke
@allure.title("Create CPQ Quote Without Approval")
def test_user_can_create_quote_with_product_without_approval(cpq_workflow: CPQWorkflow):
    ctx = cpq_workflow.load_scenario_data()

    # 1. Headless API Data Staging & Faker Assertions (Account, Contact, Opp, Quote)
    cpq_workflow.stage_quote_prerequisites(ctx)

    # 2. Quote Line Editor (QLE) UI Actions (Add Product, Calculate, Save)
    cpq_workflow.configure_quote_lines(ctx)

    # 3. Post-QLE Lifecycle & Final UI Status Verification (Order, Contract, Status)
    cpq_workflow.finalize_and_verify(ctx)
```

---

## 📊 Reporting & Run Artifacts

Every test execution automatically generates structured run artifacts inside `test_runs/run_latest/`:

- **HTML Dashboard Report**: `test_runs/run_latest/dashboard/index.html`
- **Structured Execution Logs**: `test_runs/run_latest/logs/execution.log`
- **Playwright Traces**: `test_runs/run_latest/traces/` (View via `playwright show-trace <trace.zip>`)
- **Video Recordings**: `test_runs/run_latest/videos/`
- **Failure Screenshots**: `test_runs/run_latest/screenshots/`
- **Excel Run Write-Back**: `test_data/test_data.xlsx` (`execution_results` sheet) logging status, execution duration, and Salesforce IDs.
