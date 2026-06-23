"""
Test: cmdb_context tool

Verifies pre-packaged agent context.
"""

import pytest
from tools.cmdb_context import cmdb_context


def test_context_for_known_agent():
    """Context includes all required fields for known agent."""
    ctx = cmdb_context("hermes-arquitectobi")
    
    # Core fields
    assert ctx["identity"] == "hermes-arquitectobi"
    assert "known_environment" in ctx
    
    env = ctx["known_environment"]
    assert "kind" in env
    assert "status" in env
    assert "runs_on" in env
    assert "uses" in env
    
    # Warnings (may be empty but should be present)
    assert "warnings" in ctx
    assert "dependents" in ctx
    
    # Evidence for self-grounding
    assert "evidence" in ctx
    if ctx["evidence"]:
        assert "source_file" in ctx["evidence"]
        assert "confidence_level" in ctx["evidence"]


def test_context_for_unknown_agent():
    """Context handles unknown agent gracefully."""
    ctx = cmdb_context("unknown-agent-xyz")
    
    assert ctx["identity"] == "unknown-agent-xyz"
    assert "error" in ctx
    assert ctx["known_environment"] == {}
    assert ctx["dependents"] == []
    assert ctx["warnings"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])