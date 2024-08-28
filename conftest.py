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


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runpaid"):
        return
    skip_paid = pytest.mark.skip(reason="need --runpaid option to run")
    for item in items:
        if "paid" in item.keywords:
            item.add_marker(skip_paid)
