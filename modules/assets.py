"""
AlertLogic Assets Management.
Query asset topology and declare/remove/update assets.

Spec: assets_query.v1, assets_write.v1

Note: remediations live in compliance.py (PUT /assets_query/v2/.../remediations).
"""
from typing import Annotated, List, Optional
from pydantic import Field
from mcp.server import FastMCP
from modules.base import BaseModule


class AssetsModule(BaseModule):
    """Assets query (v1) + write (v1)."""

    def register_tools(self, server: FastMCP):
        # Query
        self._add_tool(server, self.assets_query, "assets_query",
                        "Query assets for a deployment")
        self._add_tool(server, self.assets_get_topology, "assets_get_topology",
                        "Get topological layout of assets in a deployment")
        # Write
        self._add_tool(server, self.assets_declare, "assets_declare",
                        "Declare a single asset in the asset model")
        self._add_tool(server, self.assets_batch_declare, "assets_batch_declare",
                        "Declare multiple assets/properties in one batch")
        self._add_tool(server, self.assets_remove, "assets_remove",
                        "Remove an asset from the asset model")
        self._add_tool(server, self.assets_declare_properties, "assets_declare_properties",
                        "Set/update properties on an asset")

    # ---- Query ----

    def assets_query(
        self,
        deployment_id: Annotated[str, Field(description="Deployment UUID (get from deployments_list)")],
        asset_types: Annotated[Optional[str], Field(
            description="Comma-separated asset types (e.g., 'host,vpc,subnet')"
        )] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """General asset query. GET /assets_query/v1/{account_id}/deployments/{deployment_id}/assets"""
        params = {}
        if asset_types:
            params["asset_types"] = asset_types
        return self._get(
            f"/assets_query/v1/{{account_id}}/deployments/{deployment_id}/assets",
            account_id=account_id,
            params=params or None,
        )

    def assets_get_topology(
        self,
        deployment_id: Annotated[str, Field(description="Deployment UUID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
        include_filters: Annotated[Optional[str], Field(
            description="Asset types to include (comma-separated)"
        )] = None,
        extras: Annotated[Optional[str], Field(
            description="Extra data to include (e.g., 'vulnerabilities')"
        )] = None,
    ) -> dict:
        """Topology query. GET /assets_query/v1/{account_id}/deployments/{deployment_id}/topology"""
        params = {}
        if include_filters:
            params["include_filters"] = include_filters
        if extras:
            params["extras"] = extras
        return self._get(
            f"/assets_query/v1/{{account_id}}/deployments/{deployment_id}/topology",
            account_id=account_id,
            params=params or None,
        )

    # ---- Write ----
    # All writes hit PUT /assets_write/v1/{account_id}/deployments/{deployment_id}/assets
    # with an `operation` discriminator in the body.

    def _write(self, deployment_id: str, body: dict, account_id: Optional[str]) -> dict:
        return self._put(
            f"/assets_write/v1/{{account_id}}/deployments/{deployment_id}/assets",
            account_id=account_id,
            json_body=body,
        )

    def assets_declare(
        self,
        deployment_id: Annotated[str, Field(description="Deployment UUID")],
        asset_type: Annotated[str, Field(description="Asset type (e.g., 'host')")],
        asset_key: Annotated[str, Field(description="Asset key (e.g., '/aws/us-west-2/host/i-123')")],
        scope: Annotated[Optional[str], Field(description="Asset scope (e.g., deployment scope key)")] = None,
        properties: Annotated[Optional[dict], Field(description="Asset properties")] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Declare one asset. PUT /assets_write/v1/.../assets (operation=declare_asset)"""
        body = {"operation": "declare_asset", "type": asset_type, "key": asset_key}
        if scope is not None:
            body["scope"] = scope
        if properties is not None:
            body["properties"] = properties
        return self._write(deployment_id, body, account_id)

    def assets_batch_declare(
        self,
        deployment_id: Annotated[str, Field(description="Deployment UUID")],
        operations: Annotated[List[dict], Field(
            description="List of operations: [{'operation': 'declare_asset', 'type': 'host', 'key': '/aws/...', ...}, ...]"
        )],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Batch declare. PUT /assets_write/v1/.../assets (operation=batch_declare)"""
        body = {"operation": "batch_declare", "operations": operations}
        return self._write(deployment_id, body, account_id)

    def assets_remove(
        self,
        deployment_id: Annotated[str, Field(description="Deployment UUID")],
        asset_type: Annotated[str, Field(description="Asset type")],
        asset_key: Annotated[str, Field(description="Asset key")],
        scope: Annotated[Optional[str], Field(description="Asset scope")] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Remove an asset. PUT /assets_write/v1/.../assets (operation=remove_asset)"""
        body = {"operation": "remove_asset", "type": asset_type, "key": asset_key}
        if scope is not None:
            body["scope"] = scope
        return self._write(deployment_id, body, account_id)

    def assets_declare_properties(
        self,
        deployment_id: Annotated[str, Field(description="Deployment UUID")],
        asset_type: Annotated[str, Field(description="Asset type")],
        asset_key: Annotated[str, Field(description="Asset key")],
        properties: Annotated[dict, Field(description="Properties to set")],
        scope: Annotated[Optional[str], Field(description="Asset scope")] = None,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Declare properties. PUT /assets_write/v1/.../assets (operation=declare_properties)"""
        body = {
            "operation": "declare_properties",
            "type": asset_type,
            "key": asset_key,
            "properties": properties,
        }
        if scope is not None:
            body["scope"] = scope
        return self._write(deployment_id, body, account_id)


def setup(server: FastMCP):
    mod = AssetsModule()
    mod.register_tools(server)
