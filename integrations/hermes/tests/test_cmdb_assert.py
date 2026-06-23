"""
Test: cmdb_assert tool

Verifies binary validation for agent reasoning.
"""

import pytest
from tools.cmdb_assert import cmdb_assert


def test_assert_valid_entity_kind():
    """Assertion passes when entity matches expectations."""
    result = cmdb_assert("ollama", expected_kind="software")
    
    assert result["valid"] is True
    assert "fact" in result
    assert "confidence" in result


def test_assert_invalid_kind():
    """Assertion fails when kind doesn't match."""
    result = cmdb_assert("ollama", expected_kind="asset")
    
    assert result["valid"] is False
    assert result["reason"] is not None
    assert result.get("actual_kind") == "software"


def test_assert_nonexistent_entity():
    """Assertion fails for non-existent entity."""
    result = cmdb_assert("unknown-xyz", expected_kind="software")
    
    assert result["valid"] is False
    assert result["confidence"] == "verified_absence"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])