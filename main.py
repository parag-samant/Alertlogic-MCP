"""
AlertLogic MCP Server — Main Entrypoint.
Registers all modules and starts the MCP server.
"""
import os
import sys
from pathlib import Path

# Ensure the project directory is in sys.path for module imports
PROJECT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_DIR))

# Load environment variables from explicit .env path
# (Python 3.14 find_dotenv() has a frame assertion bug)
from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / ".env")

from mcp.server import FastMCP

# ------------------------------------------------------------------ #
#  Server initialization                                              #
# ------------------------------------------------------------------ #

server = FastMCP(
    name="AlertLogic MCP Server",
)

# ------------------------------------------------------------------ #
#  Module registration                                                #
# ------------------------------------------------------------------ #

from modules import auth
from modules import account_management
from modules import users
from modules import deployments
from modules import assets
from modules import policies
from modules import credentials
from modules import network_controls
from modules import incidents_mcp
from modules import soc
from modules import seceng
from modules import vulnerability
from modules import compliance
from modules import logging_integration
from modules import soar
from modules import billing
from modules import common
from modules import bulk_ops

MODULES = [
    auth, account_management, users, deployments, assets, policies, credentials,
    network_controls, incidents_mcp, soc, seceng, vulnerability,
    compliance, logging_integration, soar, billing, common, bulk_ops,
]
for mod in MODULES:
    mod.setup(server)

# ------------------------------------------------------------------ #
#  Start server                                                       #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import sys
    print("AlertLogic MCP Server starting (stdio)", file=sys.stderr)
    print(f"Registered {len(MODULES)} modules", file=sys.stderr)
    server.run(transport="stdio")