from __future__ import annotations

import traceback
from datetime import datetime

import pytest

from config.settings import settings
from utils.file_handler import create_run_dirs
from utils.log_context import failure_context, set_test
from utils.system_logger import configure_logging, get_logger

logger = get_logger(__name__)

# Register domain-specific modular fixtures from fixtures/ package
pytest_plugins = [
    "fixtures.api_fixtures",
    "fixtures.page_fixtures",
    "fixtures.data_fixtures",
    "fixtures.workflow_fixtures",
]


def pytest_configure(config):
    dirs = create_run_dirs("run_latest")
    config._cpq_run_id = "run_latest"
    config._cpq_dirs = dirs

    report_path = str(dirs.dashboard / "index.html")
    config.option.htmlpath = report_path
    config.option.self_contained_html = True

    configure_logging(dirs.logs / "execution.log")

    from utils.excel_writer import ExcelWriter
    ExcelWriter(settings.excel_path).reset_execution_results()


@pytest.fixture(scope="session")
def output_dirs(request):
    return request.config._cpq_dirs


@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {
        "headless": settings.headless,
        "slow_mo": settings.slow_mo_ms,
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, output_dirs):
    from config.settings import PROJECT_ROOT
    auth_file = PROJECT_ROOT / ".auth" / f"storage_state_{settings.environment.lower()}.json"

    args = {
        **browser_context_args,
        "viewport": {"width": settings.viewport_width, "height": settings.viewport_height},
        "locale": settings.locale,
        "timezone_id": settings.timezone_id,
        "geolocation": {
            "latitude": settings.geolocation_latitude,
            "longitude": settings.geolocation_longitude,
        },
        "permissions": ["geolocation"],
    }
    if auth_file.exists() and auth_file.stat().st_size > 10:
        try:
            import json
            with open(auth_file, "r") as f:
                json.load(f)
            args["storage_state"] = str(auth_file)
        except Exception:
            pass
    if settings.video_mode == "on":
        args["record_video_dir"] = str(output_dirs.videos)
        args["record_video_size"] = {
            "width": settings.video_width,
            "height": settings.video_height,
        }
    return args


@pytest.fixture(autouse=True)
def apply_timeouts(context):
    context.set_default_timeout(settings.action_timeout_ms)
    context.set_default_navigation_timeout(settings.navigation_timeout_ms)


@pytest.fixture(autouse=True)
def test_logging(request, authenticated_page, output_dirs):
    set_test(request.node.name)
    started = datetime.now()
    logger.info(
        "STATUS=START ENV=%s BROWSER=chromium HEADLESS=%s",
        settings.environment,
        settings.headless,
    )
    context = authenticated_page.context
    trace_path = output_dirs.traces / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.node.name}.zip"
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield
    duration = (datetime.now() - started).total_seconds()
    failed = request.node.rep_call.failed if hasattr(request.node, "rep_call") else False
    try:
        if failed:
            context.tracing.stop(path=str(trace_path))
            request.node.trace_path = str(trace_path)
        else:
            context.tracing.stop()
    except Exception:
        logger.exception("STATUS=FAIL ACTION=STOP_TRACE")
    logger.info("STATUS=%s DURATION=%ss", "FAIL" if failed else "PASS", duration)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    if report.when != "call" or not report.failed:
        return

    ctx = failure_context()
    page = item.funcargs.get("authenticated_page") or item.funcargs.get("page")
    dirs = getattr(item.config, "_cpq_dirs", None)
    screenshot = ""
    video = ""
    url = ""
    if page:
        try:
            url = page.url
            if dirs:
                screenshot_path = (
                    dirs.screenshots
                    / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{item.name}_{ctx.get('step') or 'call'}_failure.png"
                )
                page.screenshot(path=str(screenshot_path), full_page=True)
                screenshot = str(screenshot_path)
        except Exception:
            logger.exception("STATUS=FAIL ACTION=CAPTURE_SCREENSHOT")
        try:
            video_obj = page.video
            if video_obj:
                video = video_obj.path()
        except Exception:
            pass

    tb = "".join(traceback.format_exception(None, call.excinfo.value, call.excinfo.tb)) if call.excinfo else ""
    source = ""
    if call.excinfo:
        tb_last = traceback.extract_tb(call.excinfo.tb)[-1]
        source = f"{tb_last.filename}:{tb_last.lineno}"

    summary = f"""
============================================================
TEST FAILURE SUMMARY
============================================================
TEST:        {item.name}
STATUS:      FAILED
ENV:         {settings.environment}
BROWSER:     chromium
STEP:        {ctx.get('step')}
OBJECT:      {ctx.get('object')}
METHOD:      {ctx.get('method')}
ACTION:      {ctx.get('action')}
DATA:        {ctx.get('data')}
ERROR:       {call.excinfo.typename if call.excinfo else ''} {call.excinfo.value if call.excinfo else ''}
SOURCE:      {source}
URL:         {url}
SCREENSHOT:  {screenshot}
TRACE:       {getattr(item, 'trace_path', '')}
VIDEO:       {video}
TIMESTAMP:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================================
"""
    logger.error(summary)
    report.longrepr = f"{report.longrepr}\n{summary}\n{tb}"
