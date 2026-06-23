#!/usr/bin/env python3
"""
Update GitHub repository description and topics.

Run with:
    python scripts/update-github-meta.py

Requires:
- GitHub CLI (gh) authenticated, OR
- GITHUB_TOKEN environment variable with repo access
"""

import subprocess
import json
import sys

REPO = "sowerkoku/agent-cmdb"
DESCRIPTION = "A factual grounding layer that helps AI agents query verified reality before reasoning or acting."

TOPICS = [
    "ai-agents",
    "agentic-ai",
    "grounding",
    "cmdb",
    "knowledge-graph",
    "dependency-graph",
    "agent-memory",
    "llm",
    "reasoning",
    "infrastructure",
    "facts",
    "hallucination-prevention",
    "factual-memory",
]


def update_with_gh_cli():
    """Use GitHub CLI to update description and topics."""
    try:
        # Update description
        print(f"Updating description...")
        result = subprocess.run(
            ["gh", "repo", "edit", REPO, "--description", DESCRIPTION],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Description updated")
        
        # Update topics
        print(f"Updating topics...")
        topics_str = ",".join(TOPICS)
        result = subprocess.run(
            ["gh", "repo", "edit", REPO, "--topics", topics_str],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Topics updated ({len(TOPICS)} topics)")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ GitHub CLI failed: {e}")
        print(f"  stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ GitHub CLI (gh) not found")
        print("  Install: https://cli.github.com/")
        return False


def main():
    print(f"Repository: {REPO}")
    print(f"Description: {DESCRIPTION}")
    print(f"Topics: {', '.join(TOPICS)}")
    print()
    
    success = update_with_gh_cli()
    
    if success:
        print()
        print("✅ GitHub metadata updated successfully!")
        print(f"View: https://github.com/{REPO}")
        return 0
    else:
        print()
        print("❌ Failed to update GitHub metadata")
        print()
        print("Manual steps:")
        print(f"1. Go to https://github.com/{REPO}")
        print("2. Click 'About' settings (gear icon)")
        print(f"3. Set description to:")
        print(f"   {DESCRIPTION}")
        print(f"4. Add topics: {', '.join(TOPICS)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())