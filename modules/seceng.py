"""
AlertLogic Security Engineering & Compliance.
Cargo v2 (scheduled reports) and AETuner v1 (analytics tuning).

Specs:
  - cargo.v2.yaml  — host: api.cloudinsight.alertlogic.com (default)
  - aetuner.v1.yaml — host: aetuner.mdr.global.alertlogic.com

Note: cargo v2's public spec only documents list/rerun ops. Create/get/delete
schedule and execution-record fetching by ID are not in the YAML, so they're
not exposed here. Use the console for now.
"""
from typing import Annotated, List, Literal, Optional
from pydantic import Field
from mcp.server import FastMCP
from modules.base import BaseModule, url_quote


CargoScheduleType = Literal["tableau", "search", "search_v2"]
CargoStatus = Literal["scheduled", "running", "cancelled", "failed", "completed"]
AetunerDataType = Literal["logsmsgs", "observations", "telemetry"]
AetunerOutput = Literal["all", "correlations", "analytics"]
AetunerTuningType = Literal[
    "severity", "visibility", "threshold", "handling", "whitelist", "blacklist"
]
AetunerTuningOp = Literal["add", "subtract", "write", "delete"]


class SecEngModule(BaseModule):
    """Cargo report scheduling + AETuner analytics tuning."""

    def register_tools(self, server: FastMCP):
        # ---- Cargo v2 ----
        self._add_tool(server, self.cargo_list_schedules, "cargo_list_schedules",
                        "List Cargo report schedules")
        self._add_tool(server, self.cargo_list_executions, "cargo_list_executions",
                        "List Cargo execution records (report runs)")
        self._add_tool(server, self.cargo_rerun_execution, "cargo_rerun_execution",
                        "Rerun a single execution record")
        self._add_tool(server, self.cargo_rerun_executions, "cargo_rerun_executions",
                        "Rerun multiple execution records (comma-separated IDs)")
        # ---- AETuner v1 ----
        self._add_tool(server, self.aetuner_list_analytics, "aetuner_list_analytics",
                        "List analytics names (logmsgs/observations/telemetry)")
        self._add_tool(server, self.aetuner_get_analytic, "aetuner_get_analytic",
                        "Get a single analytic by its name")
        self._add_tool(server, self.aetuner_set_tuning, "aetuner_set_tuning",
                        "Apply tuning entries to an analytic (severity/visibility/threshold/etc.)")

    # ---- Cargo v2 (default host) ----

    def cargo_list_schedules(
        self,
        schedule_type: Annotated[Optional[CargoScheduleType], Field(
            description="Filter: tableau / search / search_v2"
        )] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """GET /cargo/v2/{account_id}/schedule"""
        params = {}
        if schedule_type:
            params["type"] = schedule_type
        return self._get(
            "/cargo/v2/{account_id}/schedule",
            account_id=account_id,
            params=params or None,
        )

    def cargo_list_executions(
        self,
        schedule_id: Annotated[Optional[str], Field(description="Filter by schedule ID")] = None,
        status: Annotated[Optional[CargoStatus], Field(description="Filter by status")] = None,
        latest_only: Annotated[bool, Field(description="Only the latest run per schedule")] = False,
        start_time: Annotated[Optional[int], Field(description="Epoch seconds — lower bound")] = None,
        end_time: Annotated[Optional[int], Field(description="Epoch seconds — upper bound")] = None,
        order: Annotated[Literal["asc", "desc"], Field(description="Sort order")] = "desc",
        limit: Annotated[int, Field(description="Max records (1..1000)")] = 100,
        continuation: Annotated[Optional[str], Field(description="Pagination token")] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """GET /cargo/v2/{account_id}/execution_record"""
        params = {"order": order, "limit": limit, "latest_only": str(latest_only).lower()}
        if schedule_id:
            params["schedule_id"] = schedule_id
        if status:
            params["status"] = status
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time
        if continuation:
            params["continuation"] = continuation
        return self._get(
            "/cargo/v2/{account_id}/execution_record",
            account_id=account_id,
            params=params,
        )

    def cargo_rerun_execution(
        self,
        execution_id: Annotated[str, Field(description="Execution record ID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """POST /cargo/v2/{account_id}/execution_record/{exec_id}/rerun"""
        return self._post(
            f"/cargo/v2/{{account_id}}/execution_record/{execution_id}/rerun",
            account_id=account_id,
        )

    def cargo_rerun_executions(
        self,
        execution_ids: Annotated[List[str], Field(description="Execution record IDs to rerun")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """POST /cargo/v2/{account_id}/execution_record/rerun?ids=..."""
        return self._post(
            "/cargo/v2/{account_id}/execution_record/rerun",
            account_id=account_id,
            params={"ids": ",".join(execution_ids)},
        )

    # ---- AETuner v1 (dedicated host) ----

    def aetuner_list_analytics(
        self,
        datatype: Annotated[Optional[AetunerDataType], Field(
            description="logsmsgs / observations / telemetry"
        )] = None,
        output: Annotated[AetunerOutput, Field(
            description="all / correlations / analytics"
        )] = "all",
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """GET /v1/{account_id}/analytics on aetuner host"""
        params = {"output": output}
        if datatype:
            params["datatype"] = datatype
        return self._get_at(
            "aetuner",
            "/v1/{account_id}/analytics",
            account_id=account_id,
            params=params,
        )

    def aetuner_get_analytic(
        self,
        analytic_name: Annotated[str, Field(
            description="Analytic name (multi-segment, e.g. 'logmsgs/SomeRule'). Slashes URL-encoded automatically."
        )],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
        include_audit_events: Annotated[bool, Field(description="Include audit events")] = False,
    ) -> dict:
        """GET /v1/{account_id}/analytics/{name} on aetuner host"""
        params = {"enable_new": "true"}
        if include_audit_events:
            params["include_audit_events"] = "true"
        return self._get_at(
            "aetuner",
            f"/v1/{{account_id}}/analytics/{url_quote(analytic_name)}",
            account_id=account_id,
            params=params,
        )

    def aetuner_set_tuning(
        self,
        analytic_name: Annotated[str, Field(description="Analytic name")],
        reason: Annotated[str, Field(description="Reason for the change (audit trail)")],
        tuning: Annotated[List[dict], Field(
            description=(
                "Tuning entries. Each: {type, operation?, value?, path?, key?}. "
                "type ∈ severity|visibility|threshold|handling|whitelist|blacklist. "
                "operation ∈ add|subtract|write|delete. "
                "Example: [{'type':'severity','operation':'write','value':'low'}]"
            )
        )],
        dry_run: Annotated[bool, Field(description="Validate without applying")] = False,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """POST /v1/{account_id}/analytics/{name} on aetuner host"""
        body = {"reason": reason, "tuning": tuning, "dry_run": dry_run}
        return self._post_at(
            "aetuner",
            f"/v1/{{account_id}}/analytics/{url_quote(analytic_name)}",
            account_id=account_id,
            json_body=body,
        )


def setup(server: FastMCP):
    mod = SecEngModule()
    mod.register_tools(server)
