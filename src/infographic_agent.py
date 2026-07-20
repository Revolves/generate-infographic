"""向后兼容 — 委托到 infographics_agent.cli"""
import sys
from infographics_agent.cli import main

sys.exit(main())