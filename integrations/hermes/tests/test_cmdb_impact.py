"""
Test: cmdb_impact tool

Verifies dependency analysis for risk assessment.
"""

import pytest
from tools.cmdb_impact import cmdb_impact


def test_impact_with_dependents():
    """Entity with dependents shows correct impact."""
    impact = cmdb_impact("ollama")
    
    assert impact["exists"] is True
    
    # Should have some dependents
    dependents = impact["depends_on_me"]["direct"]
    assert len(dependents) > 0, "Ollama should have dependents"
    
    # Risk indicators present
    risk = impact["risk_indicators"]
    assert "total_dependents" in risk
    assert "critical_dependents" in risk
    assert "single_point_of_failure" in risk


def test_impact_shows_layers():
    """Affected layers grouped by kind."""
    impact = cmdb_impact("mysql")
    
    assert "affected_layers" in impact
    
    layers = impact["affected_layers"]
    # Should have at least one affected layer
    total = sum(len(v) for v in layers.values())
    assert total > 0


def test_impact_nonexistent_entity():
    """Non-existent entity returns structured result."""
    impact = cmdb_impact("unknown-xyz")
    
    assert impact["exists"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])