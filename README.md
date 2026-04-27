# AlertLogic MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes
the AlertLogic Cloud Insight API as tools for MCP-compatible clients
(Claude Desktop, Claude Code, etc.).

## Features

Modules registered by this server:

- Authentication
- Account management
- Users
- Deployments
- Assets
- Policies
- Credentials
- Network controls
- Incidents
- SOC / SecEng / SOAR
- Vulnerability management
- Compliance
- Logging integration
- Billing
- Common helpers
- Bulk operations

## Prerequisites

- Python **3.10+**
- An AlertLogic account with API access
- An AlertLogic API key (access key ID + secret) and your account ID

## Setup

```bash
# 1. Clone
git clone https://github.com/parag-samant/Alertlogic-MCP.git
cd Alertlogic-MCP

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp .env.example .env
# then edit .env and fill in your AlertLogic API key + account ID
```

### `.env` values

| Variable                | Description                                                    |
| ----------------------- | -------------------------------------------------------------- |
| `ALERTLOGIC_API_KEY`    | Your AlertLogic API key, formatted as `access_key_id:secret`   |
| `ALERTLOGIC_BASE_URL`   | API base URL (default: `https://api.cloudinsight.alertlogic.com`) |
| `ALERTLOGIC_ACCOUNT_ID` | Your AlertLogic account ID                                     |
| `MCP_HOST`              | Bind host for the MCP server (default `127.0.0.1`)             |
| `MCP_PORT`              | Bind port (default `8000`)                                     |

## Run

```bash
python main.py
```

The server runs over **stdio**, which is what MCP clients expect.

## Use with Claude Desktop

Add an entry to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "alertlogic": {
      "command": "/absolute/path/to/Alertlogic-MCP/.venv/bin/python",
      "args": ["/absolute/path/to/Alertlogic-MCP/main.py"]
    }
  }
}
```

Restart Claude Desktop and the AlertLogic tools will be available.

## Smoke test

```bash
python smoke_test.py
```

## Security

- **Never commit your `.env`.** It is excluded by `.gitignore`.
- Treat your AlertLogic API key like a password. Rotate it if you suspect
  exposure.
- This repo does not ship with any credentials.

## License

Add a license of your choice (MIT, Apache-2.0, etc.) before sharing widely.
