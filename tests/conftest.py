"""
Pytest configuration for knowledge-kernel.

Routes CMDB_DATA_DIR to a bundled test fixture dataset so that:
- CI runs are reproducible (no dependency on user's ~/knowledge/...)
- Local tests do NOT pollute or read the user's production dataset
- Each test run starts from a known, minimal state

The fixture lives at tests/fixtures/dataset/ and contains 3 entities:
- fixture-server-a (asset, with relations)
- fixture-server-b (asset, no relations)
- fixture-software-x (software)

The user can override the dataset for local debugging by setting
CMDB_DATA_DIR explicitly before invoking pytest.
"""

import os
from pathlib import Path

# Locate the fixture dataset relative to this conftest.py
FIXTURE_DATA_DIR = Path(__file__).resolve().parent / "fixtures" / "dataset"


def pytest_configure(config):
    """Set CMDB_DATA_DIR to the fixture dataset unless already overridden."""
    if "CMDB_DATA_DIR" not in os.environ:
        os.environ["CMDB_DATA_DIR"] = str(FIXTURE_DATA_DIR)
