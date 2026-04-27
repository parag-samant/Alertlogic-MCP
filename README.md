<div align="center">

# AlertLogic MCP Server

**Bring the full AlertLogic Cloud Insight platform into your AI assistant.**

A [Model Context Protocol](https://modelcontextprotocol.io) server that turns
the AlertLogic API into a rich set of tools any MCP-compatible client
(Claude Desktop, Claude Code, Cursor, …) can call directly.

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-1.0%2B-1f6feb)](https://modelcontextprotocol.io)
[![AlertLogic](https://img.shields.io/badge/AlertLogic-Cloud%20Insight-FF6B00)](https://www.alertlogic.com/)
[![Status](https://img.shields.io/badge/status-active-success)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](#contributing)

</div>

---

## Table of Contents

- [Why this exists](#why-this-exists)
- [What's inside](#whats-inside)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Connecting an MCP client](#connecting-an-mcp-client)
- [Tool catalog](#tool-catalog)
- [Smoke test](#smoke-test)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Why this exists

AlertLogic exposes a powerful but **wide** API surface — incidents, assets,
deployments, vulnerabilities, SOAR playbooks, compliance, IAM, billing, and
more — spread across many microservices. Hitting all of that from an LLM
chat or agentic workflow normally means hand-rolling dozens of REST calls
and juggling tokens.

This server does that work once, and exposes a clean, typed,
MCP-compatible tool for every operation. Your AI client just calls the
tool by name; auth, retries, pagination, and JSON shaping are handled here.

**Use it to:**

- Triage incidents conversationally ("show me high-severity open incidents
  from the last 24 hours and summarize the top three")
- Run vulnerability sweeps and remediation workflows
- Manage users, roles, and access keys across many AlertLogic accounts
- Drive SOAR playbooks from natural language
- Build agentic security automation without writing a custom REST client

---

## What's inside

| Module                    | Area                                  | Highlights                                                          |
| ------------------------- | ------------------------------------- | ------------------------------------------------------------------- |
| `auth`                    | AIMS authentication                   | Token mgmt, list/get managed accounts, account ID enumeration       |
| `account_management`      | Account topology                      | Account details, lookup by name, parent/child relationships         |
| `users`                   | IAM (AIMS users + roles + keys)       | Full CRUD on users, roles, access keys, MFA, password resets        |
| `deployments`             | Deployment lifecycle                  | List / create / update / delete deployments                         |
| `assets`                  | Asset inventory                       | Query, declare, batch-declare, remove, set properties, topology     |
| `policies`                | Policy management                     | List and inspect policies                                           |
| `credentials`             | Cloud + scan credentials              | IAM role / Azure AD creds, scan creds, decrypted retrieval          |
| `network_controls`        | Exclusions + whitelisting             | Exclusion CRUD, asset checks, tag/host whitelist                    |
| `incidents_mcp`           | Incidents                             | List, get, friendly-ID lookup, complete, reopen, feedback           |
| `soc`                     | SOC search + exposures                | Submit/poll/release saved searches, exposures, health summary       |
| `seceng`                  | Security Engineering                  | Cargo schedules + executions, AETuner analytics + tuning            |
| `vulnerability`           | Vulnerability mgmt                    | Exposures by severity, per-asset exposures                          |
| `compliance`              | Remediations                          | List remediation items, conclude / dispose / undispose              |
| `logging_integration`     | Log sources                           | Source CRUD                                                         |
| `soar`                    | Playbooks + automation                | List/get playbooks, executions, inquiries, triggers                 |
| `billing`                 | Subscriptions                         | List & inspect subscriptions                                        |
| `common`                  | Notifications + connectors + endpoints| Herald notifications + subscriptions, webhook/email connectors      |
| `bulk_ops`                | Cross-account fan-out                 | Bulk list deployments, bulk health checks                           |

> 17 modules, **80+ tools** registered with the MCP server.

---

## Architecture

```
+--------------------+        stdio (MCP)         +----------------------------+
|   MCP Client       | <------------------------> |   AlertLogic MCP Server    |
| (Claude Desktop,   |                            |   (this repo, main.py)     |
|  Claude Code, …)   |                            |                            |
+--------------------+                            |  +---------------------+   |
                                                  |  |  17 modules:        |   |
                                                  |  |  auth, incidents,   |   |
                                                  |  |  assets, soar, ...  |   |
                                                  |  +----------+----------+   |
                                                  |             |              |
                                                  |     base.py (HTTP, auth,   |
                                                  |     token cache, retries)  |
                                                  +-------------+--------------+
                                                                |
                                                                v  HTTPS + AIMS token
                                                  +-----------------------------+
                                                  |   AlertLogic Cloud Insight  |
                                                  |   api.cloudinsight....com   |
                                                  +-----------------------------+
```

`base.py` centralizes:

- AIMS token acquisition + caching (re-auth only when expired)
- Per-service base URLs (Account-Topology vs. global vs. service-prefixed)
- JSON request shaping + error translation
- Common helpers all modules build on (`_get`, `_post`, `_put`, `_delete`,
  scoped variants for global and `_at` service routes)

---

## Quick start

> **Prerequisites:** Python 3.10+, an AlertLogic account with API access,
> and an API key (access key ID + secret).

```bash
# 1. Clone
git clone https://github.com/parag-samant/Alertlogic-MCP.git
cd Alertlogic-MCP

# 2. Virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your credentials (see next section)
cp .env.example .env
$EDITOR .env

# 5. Run
python main.py
```

The server speaks **stdio**, the standard MCP transport. You don't run it
"as a daemon" — your MCP client launches it on demand.

---

## Configuration

All configuration is via environment variables (loaded from `.env`).

| Variable                | Required | Default                                       | Description                                      |
| ----------------------- | :------: | --------------------------------------------- | ------------------------------------------------ |
| `ALERTLOGIC_API_KEY`    |   yes    | —                                             | API key formatted as `access_key_id:secret`      |
| `ALERTLOGIC_BASE_URL`   |    no    | `https://api.cloudinsight.alertlogic.com`     | API base URL (US/EU/UK datacenter)               |
| `ALERTLOGIC_ACCOUNT_ID` |   yes    | —                                             | Your AlertLogic account ID                       |
| `MCP_HOST`              |    no    | `127.0.0.1`                                   | Bind host (only relevant if you swap transport)  |
| `MCP_PORT`              |    no    | `8000`                                        | Bind port                                        |

### Datacenter base URLs

| Region | `ALERTLOGIC_BASE_URL`                      |
| ------ | ------------------------------------------ |
| US     | `https://api.cloudinsight.alertlogic.com`  |
| EU     | `https://api.cloudinsight.alertlogic.co.uk`|

### Getting an API key

1. Sign in to the AlertLogic console.
2. Open **Manage → Users**, pick your user, **Access Keys → Create**.
3. Copy the access key ID and secret. Combine them as
   `access_key_id:secret` and put that single string in
   `ALERTLOGIC_API_KEY`.

---

## Connecting an MCP client

### Claude Desktop

Edit `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%AppData%\Claude\claude_desktop_config.json`

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

Restart Claude Desktop. The AlertLogic tools now appear in the tool picker.

### Claude Code

```bash
claude mcp add alertlogic \
  /absolute/path/to/Alertlogic-MCP/.venv/bin/python \
  /absolute/path/to/Alertlogic-MCP/main.py
```

### Any other MCP client

Point it at the command:

```
/absolute/path/to/Alertlogic-MCP/.venv/bin/python /absolute/path/to/Alertlogic-MCP/main.py
```

Transport: **stdio**.

---

## Tool catalog

<details>
<summary><b>Authentication & accounts</b> (auth, account_management)</summary>

- `aims_authenticate`, `aims_token_info`
- `aims_list_managed_accounts`, `aims_get_account`, `aims_list_account_ids`,
  `aims_update_account`
- `aims_get_account_details`, `aims_get_account_by_name`,
  `aims_get_account_topology`, `aims_check_relationship`,
  `aims_list_accounts_by_relationship`

</details>

<details>
<summary><b>Users, roles, access keys</b> (users)</summary>

- Users: `aims_list_users`, `aims_get_user`, `aims_create_user`,
  `aims_update_user`, `aims_delete_user`, `aims_get_user_permissions`
- Roles: `aims_list_roles`, `aims_create_role`, `aims_grant_role`,
  `aims_revoke_role`, `aims_get_user_roles`
- Keys: `aims_list_access_keys`, `aims_create_access_key`,
  `aims_delete_access_key`
- Account hygiene: `aims_initiate_password_reset`, `aims_remove_mfa`

</details>

<details>
<summary><b>Deployments & assets</b> (deployments, assets)</summary>

- `deployments_list`, `deployments_get`, `deployments_create`,
  `deployments_update`, `deployments_delete`
- `assets_query`, `assets_get_topology`, `assets_declare`,
  `assets_batch_declare`, `assets_remove`, `assets_declare_properties`

</details>

<details>
<summary><b>Credentials & policies</b> (credentials, policies)</summary>

- `credentials_list`, `credentials_get`, `credentials_delete`,
  `credentials_create_iam_role`, `credentials_create_azure_ad`
- Scan credentials: `credentials_get_scan`, `credentials_set_scan`,
  `credentials_delete_scan`, `credentials_get_all_scan`,
  `credentials_get_decrypted`
- `policies_list`, `policies_get`

</details>

<details>
<summary><b>Network controls</b> (network_controls)</summary>

- Exclusions: `exclusions_list`, `exclusions_get`, `exclusions_create`,
  `exclusions_update`, `exclusions_delete`, `exclusions_check_asset`
- Whitelist: `whitelist_list_tags`, `whitelist_add_tag`,
  `whitelist_remove_tag`, `whitelist_list_hosts`, `whitelist_check_host`

</details>

<details>
<summary><b>Incidents</b> (incidents_mcp)</summary>

- `incidents_list`, `incidents_get`, `incident_get_by_friendly_id`
- `incidents_complete`, `incidents_reopen`, `incidents_add_feedback`

</details>

<details>
<summary><b>SOC, SecEng, SOAR</b> (soc, seceng, soar)</summary>

- SOC search: `search_submit`, `search_status`, `search_results`,
  `search_release`, `get_exposures`, `get_health_summary`
- SecEng: `cargo_list_schedules`, `cargo_list_executions`,
  `cargo_rerun_execution`, `cargo_rerun_executions`,
  `aetuner_list_analytics`, `aetuner_get_analytic`, `aetuner_set_tuning`
- SOAR / Responder: `responder_list_playbooks`, `responder_get_playbook`,
  `responder_create_execution`, `responder_get_execution`,
  `responder_query_executions`, `responder_list_inquiries`,
  `responder_list_triggers`

</details>

<details>
<summary><b>Vulnerability & compliance</b> (vulnerability, compliance)</summary>

- `vuln_list_exposures`, `vuln_list_by_severity`, `vuln_get_asset_exposures`
- `remediation_items_list`, `remediations_conclude`,
  `remediations_dispose`, `remediations_undispose`

</details>

<details>
<summary><b>Logging, billing, notifications, bulk ops</b></summary>

- Log sources: `sources_list`, `sources_get`, `sources_create`,
  `sources_update`, `sources_delete`
- Billing: `subscriptions_list`, `subscriptions_get`
- Herald notifications: `herald_list_notification_types`,
  `herald_send_notification`, `herald_get_notification`,
  `herald_list_subscriptions`, `herald_create_subscription`,
  `herald_get_subscription`, `herald_delete_subscription`
- Connectors: `connectors_list`, `connectors_create_webhook`,
  `connectors_create_email`, `connectors_get`, `connectors_delete`,
  `connectors_list_integration_types`, `endpoints_get`
- Cross-account: `bulk_list_deployments`, `bulk_health_check`

</details>

---

## Smoke test

A standalone script that exercises a representative cross-section of tools
without going through an MCP client:

```bash
python smoke_test.py
```

Useful for verifying credentials, network reachability, and base config
before wiring the server into your client.

---

## Security

- **Never commit `.env`.** It is excluded by `.gitignore` and the repo
  ships only `.env.example` with placeholders.
- Treat `ALERTLOGIC_API_KEY` like a password. **Rotate it** if you suspect
  exposure (chat logs, screen-shares, lost laptop, …).
- The server runs locally over stdio under your user account; it does not
  open a network port by default.
- `base.py` does not log request bodies or credentials. If you fork and
  add logging, be careful about token and secret material.
- This repo ships **no credentials of any kind**.

---

## Troubleshooting

<details>
<summary><b>"Authentication failed" / 401 from AlertLogic</b></summary>

- Check `ALERTLOGIC_API_KEY` is the full `access_key_id:secret` string
  (with the colon).
- Confirm `ALERTLOGIC_BASE_URL` matches your datacenter (US vs. EU).
- Make sure the access key hasn't been disabled in the AlertLogic console.

</details>

<details>
<summary><b>Tools don't appear in Claude Desktop</b></summary>

- Use **absolute** paths in `claude_desktop_config.json` — `~` is not
  expanded.
- Make sure `command` points at the venv's Python, not the system Python.
- Check the Claude Desktop logs for stderr from this server.

</details>

<details>
<summary><b>"ModuleNotFoundError: mcp"</b></summary>

You're running `python main.py` outside the venv. Activate it
(`source .venv/bin/activate`) or use the venv's Python directly.

</details>

---

## Contributing

PRs and issues welcome. Quick-fire guide:

1. Fork → branch → commit → PR.
2. Add new endpoints as additional methods on the matching module's
   `register_tools(self, server)` and wire them with `self._add_tool(...)`.
3. New module? Drop it in `modules/`, expose `setup(server)`, and import
   it in `main.py`'s `MODULES` list.
4. Keep tools small and well-documented — each tool's docstring is what
   the LLM sees when deciding whether to call it.

---

## License

No license file is shipped yet. Until one is added, **all rights reserved**
by the repository owner. If you'd like to use this in your own project,
open an issue and ask — adding an OSI-approved license (MIT, Apache-2.0)
is a likely next step.
