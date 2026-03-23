"""Shared pytest fixtures for PatchGuard test suite."""
import json
import pathlib
import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def sonarqube_sample():
    """Load SonarQube sample JSON fixture."""
    with open(FIXTURES_DIR / "sonarqube_sample.json", "r") as f:
        return json.load(f)


@pytest.fixture
def mend_sample():
    """Load Mend sample JSON fixture."""
    with open(FIXTURES_DIR / "mend_sample.json", "r") as f:
        return json.load(f)


@pytest.fixture
def trivy_sample():
    """Load Trivy sample JSON fixture."""
    with open(FIXTURES_DIR / "trivy_sample.json", "r") as f:
        return json.load(f)
