"""
Test: cmdb_get tool

Verifies that entity retrieval includes all required fields.
"""

import pytest
from tools.cmdb_get import cmdb_get


def test_get_entity_with_evidence():
    """Entity retrieval includes full evidence."""
    result = cmdb_get("ollama")
    
    assert result["exists"] is True
    
    # Entity
    assert "entity" in result
    assert result["entity"]["id"] == "ollama"
    assert result["entity"]["kind"] == "software"
    
    # Evidence (critical for grounding)
    assert "evidence" in result
    evidence = result["evidence"]
    assert "source_file" in evidence
    assert "source_type" in evidence
    assert "confidence_level" in evidence
    assert "entity_hash" in evidence
    assert "observed_at" in evidence
    
    # Context
    assert "context" in result
    assert "queried_at" in result["context"]


def test_get_nonexistent_entity():
    """Non-existent entity returns structured absence."""
    result = cmdb_get("unknown-entity-xyz")
    
    assert result["exists"] is False
    assert "entity_id" in result
    assert "reason" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])