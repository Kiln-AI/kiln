import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()


def pytest_addoption(parser):
    parser.addoption(
        "--runpaid",
        action="store_true",
        default=False,
        help="run tests that make paid API calls",
    )
    parser.addoption(
        "--runsinglewithoutchecks",
        action="store_true",
        default=False,
        help="if testing a single test, don't check for skips like runpaid",
    )


def pytest_collection_modifyitems(config, items):
    # Always run test if it's a single test invoked, and we have "runsinglewithoutchecks" (which is enabled in vscode params)
    if len(items) == 1 and config.getoption("--runsinglewithoutchecks"):
        return
    if config.getoption("--runpaid"):
        return
    skip_paid = pytest.mark.skip(reason="need --runpaid option to run")
    for item in items:
        if "paid" in item.keywords:
            item.add_marker(skip_paid)
