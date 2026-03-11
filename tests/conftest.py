"""Shared test fixtures for trak."""

import os

import pytest
from click.testing import CliRunner

from trak.cli.main import cli


@pytest.fixture
def tmp_project(tmp_path):
    """Change to a temporary directory, yield, then restore CWD."""
    original = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original)


@pytest.fixture
def initialized_project(tmp_project):
    """Run trak init in a temporary directory and return the path."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    return tmp_project
