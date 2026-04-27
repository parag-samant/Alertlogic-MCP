"""
AlertLogic Billing & Subscriptions.
View and manage subscription entitlements.

Maps to: Subscriptions API
"""
from typing import Annotated, Optional
from pydantic import Field
from mcp.server import FastMCP
from modules.base import BaseModule


class BillingModule(BaseModule):
    """Subscription and entitlement management."""

    def register_tools(self, server: FastMCP):
        self._add_tool(server, self.subscriptions_list, "subscriptions_list",
                        "List all subscriptions/entitlements for an account")
        self._add_tool(server, self.subscriptions_get, "subscriptions_get",
                        "Get subscription details")

    def subscriptions_list(
        self,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """List subscriptions. GET /subscriptions/v1/{account_id}/subscriptions"""
        return self._get_global("/subscriptions/v1/{account_id}/subscriptions", account_id=account_id)

    def subscriptions_get(
        self,
        subscription_id: Annotated[str, Field(description="Subscription ID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Get subscription. GET /subscriptions/v1/{account_id}/subscription/{subscription_id}"""
        return self._get_global(
            f"/subscriptions/v1/{{account_id}}/subscription/{subscription_id}",
            account_id=account_id,
        )


def setup(server: FastMCP):
    mod = BillingModule()
    mod.register_tools(server)