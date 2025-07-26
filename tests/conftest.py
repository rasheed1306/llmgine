"""Pytest configuration for the project."""

# conftest.py

import os

import dotenv
import pytest

dotenv.load_dotenv()


def pytest_addoption(parser):
    parser.addoption("--ipdb", action="store_true", help="Enable IPython debugger")


def pytest_configure(config):
    if config.getoption("--ipdb"):
        os.environ["PYTHONBREAKPOINT"] = "IPython.core.debugger.set_trace"
        config.option.pdb = True
        config.option.pdbcls = "IPython.core.debugger:Pdb"


@pytest.fixture
def sample_fixture():
    return {"foo": "bar"}
