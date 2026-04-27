"""
AlertLogic Logging & Data Integration.
Log sources, ingest configuration, and search.

Maps to: Sources API, Ingest API, Search API
"""
from typing import Annotated, Optional
from pydantic import Field
from mcp.server import FastMCP
from modules.base import BaseModule


class LoggingIntegrationModule(BaseModule):
    """Log source and data integration management."""

    def register_tools(self, server: FastMCP):
        self._add_tool(server, self.sources_list, "sources_list",
                        "List all log/data sources for an account")
        self._add_tool(server, self.sources_get, "sources_get",
                        "Get details of a specific data source")
        self._add_tool(server, self.sources_create, "sources_create",
                        "Create a new log source")
        self._add_tool(server, self.sources_update, "sources_update",
                        "Update a log source configuration")
        self._add_tool(server, self.sources_delete, "sources_delete",
                        "Delete a log source")

    def sources_list(
        self,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
        source_type: Annotated[Optional[str], Field(description="Filter by source type")] = None,
    ) -> dict:
        """List sources. GET /sources/v1/{account_id}/sources"""
        params = {}
        if source_type:
            params["type"] = source_type
        return self._get("/sources/v1/{account_id}/sources", account_id=account_id, params=params or None)

    def sources_get(
        self,
        source_id: Annotated[str, Field(description="Source UUID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Get source. GET /sources/v1/{account_id}/sources/{source_id}"""
        return self._get(
            f"/sources/v1/{{account_id}}/sources/{source_id}",
            account_id=account_id,
        )

    def sources_create(
        self,
        name: Annotated[str, Field(description="Source name")],
        source_type: Annotated[str, Field(
            description="Source type (e.g., 'environment', 'log_source')"
        )],
        config: Annotated[dict, Field(
            description=(
                "Source-type-specific config object. Must include 'collection_method' and "
                "'collection_type' for environment sources, e.g. "
                "{'collection_method': 'api', 'collection_type': 'aws', ...}"
            )
        )],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Create source. POST /sources/v1/{account_id}/sources"""
        body = {"source": {"name": name, "type": source_type, "config": config}}
        return self._post("/sources/v1/{account_id}/sources", account_id=account_id, json_body=body)

    def sources_update(
        self,
        source_id: Annotated[str, Field(description="Source UUID")],
        name: Annotated[Optional[str], Field(description="New name")] = None,
        config: Annotated[Optional[dict], Field(description="Updated configuration object")] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Update source. PUT /sources/v1/{account_id}/sources/{source_id}"""
        source_body: dict = {}
        if name:
            source_body["name"] = name
        if config:
            source_body["config"] = config
        return self._put(
            f"/sources/v1/{{account_id}}/sources/{source_id}",
            account_id=account_id,
            json_body={"source": source_body},
        )

    def sources_delete(
        self,
        source_id: Annotated[str, Field(description="Source UUID to delete")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Delete source. DELETE /sources/v1/{account_id}/sources/{source_id}"""
        return self._delete(
            f"/sources/v1/{{account_id}}/sources/{source_id}",
            account_id=account_id,
        )


def setup(server: FastMCP):
    mod = LoggingIntegrationModule()
    mod.register_tools(server)