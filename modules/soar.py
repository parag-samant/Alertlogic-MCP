"""
AlertLogic SOAR (Responder v1).
Playbooks, executions, inquiries, triggers.

Spec: responder.v1.yaml — host: api.responder.alertlogic.com
       Paths start at /v1/{account_id}/... (no /responder prefix).

Notes:
  - Listing executions is a POST /executions/history (the spec has no GET
    collection endpoint).
  - Creating an execution requires a `payload.type` that matches the
    playbook's declared type. Use responder_get_playbook to discover it.
"""
from typing import Annotated, List, Literal, Optional
from pydantic import Field
from mcp.server import FastMCP
from modules.base import BaseModule


PayloadType = Literal[
    "incident", "observation", "vulnerability", "remediation", "generic", "action",
]
ExecutionStatus = Literal[
    "new", "requested", "scheduled", "delayed", "running",
    "succeeded", "failed", "timeout", "canceled", "pending",
]
InquiryStatus = Literal["pending", "completed"]
SortOrder = Literal["asc", "desc"]


class SOARModule(BaseModule):
    """Responder v1: playbooks, executions, inquiries, triggers."""

    def register_tools(self, server: FastMCP):
        # Playbooks
        self._add_tool(server, self.responder_list_playbooks, "responder_list_playbooks",
                        "List playbooks for an account")
        self._add_tool(server, self.responder_get_playbook, "responder_get_playbook",
                        "Get a playbook by ID or name")
        # Executions
        self._add_tool(server, self.responder_create_execution, "responder_create_execution",
                        "Run a playbook or action — POST /executions")
        self._add_tool(server, self.responder_get_execution, "responder_get_execution",
                        "Get an execution by ID")
        self._add_tool(server, self.responder_query_executions, "responder_query_executions",
                        "Query execution history (POST /executions/history)")
        # Inquiries / triggers
        self._add_tool(server, self.responder_list_inquiries, "responder_list_inquiries",
                        "List inquiries (paused playbooks awaiting input)")
        self._add_tool(server, self.responder_list_triggers, "responder_list_triggers",
                        "List triggers wired to playbooks/actions")

    # ---- Playbooks ----

    def responder_list_playbooks(
        self,
        playbook_type: Annotated[Optional[str], Field(
            description="Comma-separated playbook types"
        )] = None,
        vendors: Annotated[Optional[str], Field(description="Comma-separated vendors")] = None,
        enabled: Annotated[Optional[bool], Field(description="Filter by enabled flag")] = None,
        deleted: Annotated[bool, Field(description="Include deleted playbooks")] = False,
        sort_order: Annotated[SortOrder, Field(description="Sort order")] = "desc",
        limit: Annotated[Optional[int], Field(description="Max results")] = None,
        marker: Annotated[Optional[str], Field(description="Pagination marker")] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """GET /v1/{account_id}/playbooks on responder host"""
        params = {"sort_order": sort_order, "deleted": str(deleted).lower()}
        if playbook_type:
            params["type"] = playbook_type
        if vendors:
            params["vendors"] = vendors
        if enabled is not None:
            params["enabled"] = str(enabled).lower()
        if limit is not None:
            params["limit"] = limit
        if marker:
            params["marker"] = marker
        return self._get_at(
            "responder",
            "/v1/{account_id}/playbooks",
            account_id=account_id,
            params=params,
        )

    def responder_get_playbook(
        self,
        playbook: Annotated[str, Field(description="Playbook ID or name")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """GET /v1/{account_id}/playbooks/{id_or_name}"""
        return self._get_at(
            "responder",
            f"/v1/{{account_id}}/playbooks/{playbook}",
            account_id=account_id,
        )

    # ---- Executions ----

    def responder_create_execution(
        self,
        ref: Annotated[str, Field(
            description="Playbook ID, playbook name, action ID, or action ref"
        )],
        payload: Annotated[dict, Field(
            description=(
                "Payload object. Must include `type` matching the playbook's "
                "declared payload type. Variants: "
                "{type:'incident', incident: {...}}, "
                "{type:'observation', observation: {...}}, "
                "{type:'action', parameters: {...}}, "
                "{type:'generic', parameters: {...}}, "
                "{type:'vulnerability'|'remediation', parameters: {...}}"
            )
        )],
        trigger_id: Annotated[Optional[str], Field(description="Trigger UUID")] = None,
        target_account_id: Annotated[Optional[str], Field(description="Target account for cross-account execution")] = None,
        account_id: Annotated[Optional[str], Field(description="Caller account ID")] = None,
    ) -> dict:
        """POST /v1/{account_id}/executions"""
        body = {"ref": ref, "payload": payload}
        if trigger_id:
            body["trigger_id"] = trigger_id
        if target_account_id:
            body["target_account_id"] = target_account_id
        return self._post_at(
            "responder",
            "/v1/{account_id}/executions",
            account_id=account_id,
            json_body=body,
        )

    def responder_get_execution(
        self,
        execution_id: Annotated[str, Field(description="Execution ID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """GET /v1/{account_id}/executions/{execution_id}"""
        return self._get_at(
            "responder",
            f"/v1/{{account_id}}/executions/{execution_id}",
            account_id=account_id,
        )

    def responder_query_executions(
        self,
        query: Annotated[dict, Field(
            description=(
                "Query body. Variant determined by shape: "
                "PlaybookExecutionHistoryQuery, TaskExecutionHistoryQuery, "
                "or ActionExecutionHistoryQuery. Example: "
                "{playbook_id: '...', start_timestamp: 1700000000, limit: 50}"
            )
        )],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """POST /v1/{account_id}/executions/history"""
        return self._post_at(
            "responder",
            "/v1/{account_id}/executions/history",
            account_id=account_id,
            json_body=query,
        )

    # ---- Inquiries / triggers ----

    def responder_list_inquiries(
        self,
        status: Annotated[Optional[InquiryStatus], Field(description="pending/completed")] = None,
        deployment_id: Annotated[Optional[str], Field(description="Filter by deployment")] = None,
        inquiry_type: Annotated[Optional[str], Field(description="Filter by inquiry type")] = None,
        start_timestamp: Annotated[Optional[int], Field(description="Epoch lower bound")] = None,
        end_timestamp: Annotated[Optional[int], Field(description="Epoch upper bound")] = None,
        sort_by: Annotated[Optional[str], Field(description="Sort field")] = None,
        sort_order: Annotated[SortOrder, Field(description="Sort order")] = "desc",
        limit: Annotated[Optional[int], Field(description="Max results")] = None,
        marker: Annotated[Optional[str], Field(description="Pagination marker")] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """GET /v1/{account_id}/inquiries"""
        params = {"sort_order": sort_order}
        if status:
            params["status"] = status
        if deployment_id:
            params["deployment_id"] = deployment_id
        if inquiry_type:
            params["type"] = inquiry_type
        if start_timestamp is not None:
            params["start_timestamp"] = start_timestamp
        if end_timestamp is not None:
            params["end_timestamp"] = end_timestamp
        if sort_by:
            params["sort_by"] = sort_by
        if limit is not None:
            params["limit"] = limit
        if marker:
            params["marker"] = marker
        return self._get_at(
            "responder",
            "/v1/{account_id}/inquiries",
            account_id=account_id,
            params=params,
        )

    def responder_list_triggers(
        self,
        trigger_type: Annotated[Optional[str], Field(description="Comma-separated trigger types")] = None,
        enabled: Annotated[Optional[bool], Field(description="Filter by enabled flag")] = None,
        playbooks: Annotated[Optional[str], Field(description="Comma-separated playbook IDs")] = None,
        actions: Annotated[Optional[str], Field(description="Comma-separated action refs")] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """GET /v1/{account_id}/triggers"""
        params = {}
        if trigger_type:
            params["type"] = trigger_type
        if enabled is not None:
            params["enabled"] = str(enabled).lower()
        if playbooks:
            params["playbooks"] = playbooks
        if actions:
            params["actions"] = actions
        return self._get_at(
            "responder",
            "/v1/{account_id}/triggers",
            account_id=account_id,
            params=params or None,
        )


def setup(server: FastMCP):
    mod = SOARModule()
    mod.register_tools(server)
