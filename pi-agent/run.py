#!/usr/bin/env python3
"""Pi Agent entrypoint."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import Agent


if __name__ == "__main__":
    agent = Agent(config_path="config.yaml")
    agent.start()
