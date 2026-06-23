"""
Test: cmdb_exists tool

Verifies that existence checks work correctly.
"""

import pytest
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.cmdb_exists import cmdb_exists


def test_exists_for_known_entity():
    """Entity that exists in CMDB."""
    result = cmdb_exists("ollama")
    
    assert result["exists"] is True
    assert result.get("kind") == "software"
    assert result.get("status") == "operational"


def test_not_exists_for_unknown_entity():
    """Entity that doesn't exist in CMDB."""
    result = cmdb_exists("redis-unknown-entity")
    
    assert result["exists"] is False
    assert "reason" in result
    assert result["reason"] == "Entity not found in CMDB"


def test_exists_returns_similar_entities():
    """When entity not found, similar entities suggested."""
    result = cmdb_exists("mssql")  # Not in CMDB, but "mysql" exists
    
    assert result["exists"] is False
    
    # Should have similar_entities if any match
    # (may be empty if no fuzzy matches)
    assert "similar_entities" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])