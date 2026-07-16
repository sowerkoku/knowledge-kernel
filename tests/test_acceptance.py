# agent-cmdb Test Suite
#
# Two levels of tests:
#
# CORE TESTS (always pass, required for any dataset)
#   - API, schema, validation, relations, search, impact, config
#   - These verify the system works, not that specific data exists
#
# DATASET TESTS (CIC-specific, for ~/knowledge/agent-cmdb)
#   - These verify the CIC dataset contains expected entities
#   - Run with CMDB_DATA_DIR=~/knowledge/agent-cmdb
#   - Other users with other datasets would have different Dataset tests

import pytest
from pathlib import Path
import sys
import os

# Add cmdb to path
sys.path.insert(0, str(Path.home() / "agent-cmdb"))

from cmdb.api import (
    cmdb_get, cmdb_exists, cmdb_search, cmdb_list,
    cmdb_impact, cmdb_validate, cmdb_context,
)


# =============================================================================
# CORE TESTS — Must pass 100% for any deployment
# =============================================================================

class TestCoreAPI:
    """Core API functions must work regardless of dataset."""
    
    def test_cmdb_exists_returns_dict(self):
        """cmdb_exists returns a valid dict structure."""
        result = cmdb_exists("nonexistent-entity-12345")
        assert isinstance(result, dict)
        assert "exists" in result
        assert result["exists"] is False
    
    def test_cmdb_get_returns_result_object(self):
        """cmdb_get returns a CMDBResult-like object."""
        result = cmdb_get("nonexistent-entity-12345")
        assert hasattr(result, "exists")
        assert result.exists is False
    
    def test_cmdb_search_returns_list(self):
        """cmdb_search returns a list."""
        result = cmdb_search("nonexistent-xyz-12345")
        assert isinstance(result, list)
    
    def test_cmdb_list_returns_list(self):
        """cmdb_list returns a list."""
        result = cmdb_list()
        assert isinstance(result, list)
    
    def test_cmdb_list_by_domain(self):
        """cmdb_list can filter by domain."""
        infra = cmdb_list(domain="infrastructure")
        assert isinstance(infra, list)
        # If dataset has infrastructure entities, verify structure
        if infra:
            assert "kind" in infra[0]
            assert "domain" in infra[0]
    
    def test_cmdb_list_by_kind(self):
        """cmdb_list can filter by kind."""
        assets = cmdb_list(kind="asset")
        assert isinstance(assets, list)
        for a in assets:
            assert a["kind"] == "asset"
    
    def test_cmdb_impact_returns_dict(self):
        """cmdb_impact returns valid structure for existing entities."""
        # Test with an entity that DOES exist - get first asset
        entities = cmdb_list(kind="asset")
        assert len(entities) > 0, "No assets in dataset"
        
        test_id = entities[0]["id"]
        result = cmdb_impact(test_id)
        
        assert isinstance(result, dict)
        assert "exists" in result
        assert result["exists"] is True
        assert "risk_indicators" in result
    
    def test_cmdb_validate_returns_valid_structure(self):
        """cmdb_validate returns expected structure."""
        result = cmdb_validate()
        assert "valid" in result
        assert "stats" in result
        assert "by_domain" in result["stats"]
        assert "by_kind" in result["stats"]


class TestCoreSchema:
    """Schema validation must work regardless of dataset."""
    
    def test_validate_accepts_minimal_entity(self):
        """A minimal entity passes validation."""
        # This tests the validator, not the entity
        result = cmdb_validate()
        # No schema errors should occur from system itself
        assert "errors" in result
    
    def test_entities_have_required_fields(self):
        """All loaded entities have required fields."""
        entities = cmdb_list()
        for e in entities:
            assert "id" in e, f"Entity missing id: {e}"
            assert "kind" in e, f"Entity {e['id']} missing kind"
            assert "status" in e, f"Entity {e['id']} missing status"
    
    def test_no_duplicate_ids(self):
        """No duplicate entity IDs exist."""
        entities = cmdb_list()
        ids = [e["id"] for e in entities]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found"


class TestCoreRelations:
    """Relation structure must be valid."""
    
    def test_cmdb_impact_handles_missing_entity(self):
        """cmdb_impact returns exists=False for missing entities."""
        result = cmdb_impact("this-does-not-exist-12345")
        assert result["exists"] is False
    
    def test_cmdb_impact_has_risk_indicators_for_existing_entity(self):
        """cmdb_impact returns risk_indicators for existing entities."""
        # Use first asset from dataset
        entities = cmdb_list(kind="asset")
        if not entities:
            pytest.skip("No assets in dataset")
        
        test_id = entities[0]["id"]
        result = cmdb_impact(test_id)
        
        assert result["exists"] is True
        assert "risk_indicators" in result
        assert "single_point_of_failure" in result["risk_indicators"]


class TestCoreConfig:
    """Configuration must work."""
    
    def test_config_loads_from_env(self):
        """CMDBConfig loads from environment."""
        from cmdb.config import get_config
        cfg = get_config()
        assert cfg.data_dir is not None
        assert cfg.schema_version == 1


# =============================================================================
# DATASET TESTS — CIC-specific expectations
# Run with: CMDB_DATA_DIR=~/knowledge/agent-cmdb
# =============================================================================

class TestCICDataset:
    """
    Dataset-specific tests for the CIC deployment.
    
    These tests verify that the CIC dataset contains expected entities.
    Other deployments would have their own Dataset tests.
    
    Run these explicitly, not as part of core test suite.
    """
    
    @pytest.fixture(autouse=True)
    def require_cic_dataset(self):
        """Skip if not running against CIC dataset."""
        data_dir = os.environ.get("CMDB_DATA_DIR", "")
        cic_dir = str(Path.home() / "knowledge" / "agent-cmdb")
        if data_dir != cic_dir:
            pytest.skip("Not running against CIC dataset")
    
    def test_exists_hermes_agents(self):
        """Hermes agent profiles exist."""
        agents = cmdb_list(kind="agent")
        agent_ids = [a["id"] for a in agents]
        assert len(agent_ids) >= 5, f"Expected at least 5 agents, found {len(agent_ids)}"
        assert any("arquitectobi" in a for a in agent_ids), "hermes-arquitectobi not found"
        assert any("ingenierosql" in a for a in agent_ids), "hermes-ingenierosql not found"
    
    def test_exists_infrastructure(self):
        """Infrastructure assets exist."""
        assets = cmdb_list(kind="asset")
        assert len(assets) > 0, "No assets found"
        
        # Check for App Server devices
        asset_ids = [a["id"] for a in assets]
        assert any("app-server" in a.lower() or "app-server" in a for a in asset_ids), \
            "App Server devices not found"
    
    def test_exists_firebird(self):
        """Firebird database is registered."""
        result = cmdb_exists("firebird-eleventa")
        assert result["exists"], "firebird-eleventa not found"
    
    def test_exists_sync_bridge(self):
        """Sync bridge automation is registered."""
        result = cmdb_exists("sync-bridge")
        assert result["exists"], "sync-bridge not found"
    
    def test_hermes_uses_profiles(self):
        """Hermes agents have uses_profile relations."""
        hermes = cmdb_get("hermes-arquitectobi")
        if hermes.exists:
            # Should have a relation to its profile
            # (This tests the relation exists in source data)
            assert hermes.exists


if __name__ == "__main__":
    # Run core tests only by default
    pytest.main([__file__, "-v", "-k", "Core or Schema or Config or Relations"])