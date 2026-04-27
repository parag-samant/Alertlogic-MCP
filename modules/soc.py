"""
AlertLogic SOC Tools.
Threat hunting, log search, exposure lookup.

Maps to: search v2, assets_query v2, remediations v1
"""
from typing import Annotated, Optional, List
from pydantic import Field
from mcp.server import FastMCP
from modules.base import BaseModule


class SOCModule(BaseModule):
    """SOC-focused operations (search + exposure + collection-health)."""

    def register_tools(self, server: FastMCP):
        self._add_tool(server, self.search_submit, "search_submit",
                        "Submit an AL-SQL search to the Search v2 service")
        self._add_tool(server, self.search_status, "search_status",
                        "Check status of an asynchronous search")
        self._add_tool(server, self.search_results, "search_results",
                        "Fetch results of a completed search")
        self._add_tool(server, self.search_release, "search_release",
                        "Cancel/release a running or completed search")
        self._add_tool(server, self.get_exposures, "get_exposures",
                        "Get exposures, optionally filtered by deployment")
        self._add_tool(server, self.get_health_summary, "get_health_summary",
                        "Get account-wide collection health summary")

    # ---- Search v2 ----
    # Per the search.v2 spec: search_type, start, end go in QUERY params,
    # and the body is a raw AL-SQL string sent as text/plain.

    def search_submit(
        self,
        sql: Annotated[str, Field(description="AL-SQL query string")],
        start_time: Annotated[Optional[str], Field(
            description="Start time (ISO 8601 or epoch). Required unless using a relative timeframe."
        )] = None,
        end_time: Annotated[Optional[str], Field(
            description="End time (ISO 8601 or epoch)"
        )] = None,
        search_type: Annotated[str, Field(
            description="'batch' (default), 'report', or 'interactive'"
        )] = "batch",
        timeframe: Annotated[Optional[int], Field(
            description="Relative timeframe in seconds (alternative to start/end)"
        )] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Submit search. POST /search/v2/{account_id}/searches (text/plain body)."""
        params = {"search_type": search_type}
        if start_time:
            params["start"] = start_time
        if end_time:
            params["end"] = end_time
        if timeframe is not None:
            params["timeframe"] = str(timeframe)
        return self._request(
            "POST",
            "/search/v2/{account_id}/searches",
            account_id=account_id,
            params=params,
            data=sql,
            content_type="text/plain",
        )

    def search_status(
        self,
        search_uuid: Annotated[str, Field(description="Search UUID returned by search_submit")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Search status. GET /search/v2/{account_id}/searches/{search_uuid}/status"""
        return self._get(
            f"/search/v2/{{account_id}}/searches/{search_uuid}/status",
            account_id=account_id,
        )

    def search_results(
        self,
        search_uuid: Annotated[str, Field(description="Search UUID")],
        offset: Annotated[int, Field(description="Result offset for pagination")] = 0,
        limit: Annotated[int, Field(description="Max rows to return")] = 100,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Search results. GET /search/v2/{account_id}/searches/{search_uuid}"""
        return self._get(
            f"/search/v2/{{account_id}}/searches/{search_uuid}",
            account_id=account_id,
            params={"offset": offset, "limit": limit},
        )

    def search_release(
        self,
        search_uuid: Annotated[str, Field(description="Search UUID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Cancel/release a search. DELETE /search/v2/{account_id}/searches/{search_uuid}"""
        return self._delete(
            f"/search/v2/{{account_id}}/searches/{search_uuid}",
            account_id=account_id,
        )

    # ---- Exposures + health ----

    def get_exposures(
        self,
        deployment_id: Annotated[Optional[str], Field(description="Deployment UUID filter")] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """List exposures. GET /assets_query/v2/{account_id}/exposures"""
        params = {}
        if deployment_id:
            params["filter"] = [f"deployment_id:{deployment_id}"]
        return self._get(
            "/assets_query/v2/{account_id}/exposures",
            account_id=account_id,
            params=params or None,
        )

    def get_health_summary(
        self,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Collection-health summary. GET /remediations/v1/{account_id}/health/summary"""
        return self._get(
            "/remediations/v1/{account_id}/health/summary",
            account_id=account_id,
        )


def setup(server: FastMCP):
    mod = SOCModule()
    mod.register_tools(server)
