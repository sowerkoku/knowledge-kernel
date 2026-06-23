"""
Hermes Tool: cmdb_context

Pre-packaged agent context — avoids 20 sequential queries at startup.

Returns:
- identity: agent's own entity
- known_environment: runs_on, uses, reads, writes, calls
- dependents: who depends on this agent
- warnings: risk signals (SPOFs, criticality)
"""

from cmdb import cmdb_context as _cmdb_context
from pathlib import Path


ENTITIES_DIR = Path("/home/carlos/registry")


def cmdb_context(agent_id: str) -> dict:
    """
    Get pre-packaged context for specific agent.
    
    **CALL THIS ON AGENT STARTUP** instead of making 20 sequential queries.
    
    Single call provides complete self-knowledge:
    - What am I? (kind, status)
    - Where do I run? (runs_on)
    - What do I use? (uses, reads, writes)
    - Who depends on me? (dependents)
    - What are the risks? (warnings)
    
    Args:
        agent_id: Agent's own entity ID (e.g., "hermes-arquitectobi")
    
    Returns:
        dict with keys:
        - identity: str
        - known_environment: {kind, status, runs_on, uses, reads, writes, calls}
        - dependents: list of dependent entities
        - warnings: list of risk signals
        - evidence: evidence object
    
    Example:
        ```python
        # Agent startup (call ONCE)
        ctx = cmdb_context("hermes-arquitectobi")
        
        print(f"Identity: {ctx['identity']}")
        print(f"Status: {ctx['known_environment']['status']}")
        print(f"I run on: {', '.join(ctx['known_environment']['runs_on'])}")
        print(f"I use: {', '.join(ctx['known_environment']['uses'])}")
        print(f"Dependents: {len(ctx['dependents'])}")
        print(f"Warnings: {ctx['warnings']}")
        
        # Now agent has complete self-knowledge
        # No need for cmdb_get("hermes-arquitectobi") later
        ```
    
    Behavioral rules:
    - Call ONCE at agent initialization
    - Cache result for session lifetime
    - Use cached context for self-referential reasoning
    - Re-query only if explicit refresh needed
    
    Benefits:
    - Eliminates 20 sequential queries at startup
    - Provides complete grounding immediately
    - Includes risk warnings from day one
    - Prevents hallucination about own infrastructure
    """
    result = _cmdb_context(agent_id, ENTITIES_DIR)
    return result