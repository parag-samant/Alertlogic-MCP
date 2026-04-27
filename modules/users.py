"""
AlertLogic AIMS User Management.
User CRUD, role assignment, access keys, and MFA management.

Official API: https://console.cloudinsight.alertlogic.com/api/aims/
"""
from typing import Annotated, Optional, List
from pydantic import Field
from mcp.server import FastMCP
from modules.base import BaseModule


class UsersModule(BaseModule):
    """AIMS User & Role Management."""

    def register_tools(self, server: FastMCP):
        self._add_tool(server, self.aims_list_users, "aims_list_users",
                        "List all users for an account")
        self._add_tool(server, self.aims_get_user, "aims_get_user",
                        "Get user details by user ID")
        self._add_tool(server, self.aims_create_user, "aims_create_user",
                        "Create a new user in an account")
        self._add_tool(server, self.aims_update_user, "aims_update_user",
                        "Update user details (name, email, active status)")
        self._add_tool(server, self.aims_delete_user, "aims_delete_user",
                        "Delete a user from an account")
        self._add_tool(server, self.aims_get_user_permissions, "aims_get_user_permissions",
                        "Get a user's effective permissions")
        self._add_tool(server, self.aims_list_roles, "aims_list_roles",
                        "List all roles for an account (including global roles)")
        self._add_tool(server, self.aims_create_role, "aims_create_role",
                        "Create a new role with specified permissions")
        self._add_tool(server, self.aims_grant_role, "aims_grant_role",
                        "Grant a role to a user")
        self._add_tool(server, self.aims_revoke_role, "aims_revoke_role",
                        "Revoke a role from a user")
        self._add_tool(server, self.aims_get_user_roles, "aims_get_user_roles",
                        "Get all roles assigned to a user")
        self._add_tool(server, self.aims_list_access_keys, "aims_list_access_keys",
                        "List access keys for a user")
        self._add_tool(server, self.aims_create_access_key, "aims_create_access_key",
                        "Create an access key for a user")
        self._add_tool(server, self.aims_delete_access_key, "aims_delete_access_key",
                        "Delete a user's access key")
        self._add_tool(server, self.aims_initiate_password_reset, "aims_initiate_password_reset",
                        "Initiate password reset for a user (sends email)")
        self._add_tool(server, self.aims_remove_mfa, "aims_remove_mfa",
                        "Remove a user's MFA device enrollment")

    # ---- User CRUD ----

    def aims_list_users(
        self,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
        role_id: Annotated[Optional[str], Field(description="Filter by role ID")] = None,
        include_role_ids: Annotated[bool, Field(description="Include role IDs in response")] = True,
    ) -> dict:
        """List all users. GET /aims/v1/{account_id}/users"""
        params = {}
        if role_id:
            params["role_id"] = role_id
        if include_role_ids:
            params["include_role_ids"] = "true"
        return self._get("/aims/v1/{account_id}/users", account_id=account_id, params=params or None)

    def aims_get_user(
        self,
        user_id: Annotated[str, Field(description="AIMS User ID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
        include_role_ids: Annotated[bool, Field(description="Include role IDs")] = True,
    ) -> dict:
        """Get user details. GET /aims/v1/{account_id}/users/{user_id}"""
        params = {}
        if include_role_ids:
            params["include_role_ids"] = "true"
        return self._get(
            f"/aims/v1/{{account_id}}/users/{user_id}",
            account_id=account_id,
            params=params or None,
        )

    def aims_create_user(
        self,
        name: Annotated[str, Field(description="User's full name")],
        email: Annotated[str, Field(description="User's email address")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
        role_id: Annotated[Optional[str], Field(description="Role ID to grant")] = None,
        active: Annotated[bool, Field(description="Whether user is active")] = True,
        mobile_phone: Annotated[Optional[str], Field(description="Mobile phone number")] = None,
    ) -> dict:
        """Create a new user. POST /aims/v1/{account_id}/users"""
        body = {"name": name, "email": email, "active": active}
        if role_id:
            body["role_id"] = role_id
        if mobile_phone:
            body["mobile_phone"] = mobile_phone
        return self._post("/aims/v1/{account_id}/users", account_id=account_id, json_body=body)

    def aims_update_user(
        self,
        user_id: Annotated[str, Field(description="User ID to update")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
        name: Annotated[Optional[str], Field(description="New name")] = None,
        email: Annotated[Optional[str], Field(description="New email")] = None,
        active: Annotated[Optional[bool], Field(description="Active status")] = None,
        mobile_phone: Annotated[Optional[str], Field(description="Mobile phone")] = None,
    ) -> dict:
        """Update user details. POST /aims/v1/{account_id}/users/{user_id}"""
        body = {}
        if name is not None:
            body["name"] = name
        if email is not None:
            body["email"] = email
        if active is not None:
            body["active"] = active
        if mobile_phone is not None:
            body["mobile_phone"] = mobile_phone
        return self._post(f"/aims/v1/{{account_id}}/users/{user_id}", account_id=account_id, json_body=body)

    def aims_delete_user(
        self,
        user_id: Annotated[str, Field(description="User ID to delete")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Delete a user. DELETE /aims/v1/{account_id}/users/{user_id}"""
        return self._delete(f"/aims/v1/{{account_id}}/users/{user_id}", account_id=account_id)

    # ---- Permissions & Roles ----

    def aims_get_user_permissions(
        self,
        user_id: Annotated[str, Field(description="User ID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Get user permissions. GET /aims/v1/{account_id}/users/{user_id}/permissions"""
        return self._get(f"/aims/v1/{{account_id}}/users/{user_id}/permissions", account_id=account_id)

    def aims_list_roles(
        self,
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """List all roles. GET /aims/v1/{account_id}/roles"""
        return self._get("/aims/v1/{account_id}/roles", account_id=account_id)

    def aims_create_role(
        self,
        name: Annotated[str, Field(description="Role name")],
        permissions: Annotated[dict, Field(description="Role permissions object")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Create a role. POST /aims/v1/{account_id}/roles"""
        body = {"name": name, "permissions": permissions}
        return self._post("/aims/v1/{account_id}/roles", account_id=account_id, json_body=body)

    def aims_grant_role(
        self,
        user_id: Annotated[str, Field(description="User ID")],
        role_id: Annotated[str, Field(description="Role ID to grant")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Grant a role to a user. PUT /aims/v1/{account_id}/users/{user_id}/roles/{role_id}"""
        return self._put(f"/aims/v1/{{account_id}}/users/{user_id}/roles/{role_id}", account_id=account_id)

    def aims_revoke_role(
        self,
        user_id: Annotated[str, Field(description="User ID")],
        role_id: Annotated[str, Field(description="Role ID to revoke")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Revoke a role. DELETE /aims/v1/{account_id}/users/{user_id}/roles/{role_id}"""
        return self._delete(f"/aims/v1/{{account_id}}/users/{user_id}/roles/{role_id}", account_id=account_id)

    def aims_get_user_roles(
        self,
        user_id: Annotated[str, Field(description="User ID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Get user's roles. GET /aims/v1/{account_id}/users/{user_id}/roles"""
        return self._get(f"/aims/v1/{{account_id}}/users/{user_id}/roles", account_id=account_id)

    # ---- Access Keys ----

    def aims_list_access_keys(
        self,
        user_id: Annotated[str, Field(description="User ID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """List access keys. GET /aims/v1/{account_id}/users/{user_id}/access_keys"""
        return self._get(f"/aims/v1/{{account_id}}/users/{user_id}/access_keys", account_id=account_id)

    def aims_create_access_key(
        self,
        user_id: Annotated[str, Field(description="User ID")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
        label: Annotated[Optional[str], Field(description="Label for the access key")] = None,
    ) -> dict:
        """Create access key. POST /aims/v1/{account_id}/users/{user_id}/access_keys"""
        body = {}
        if label:
            body["label"] = label
        return self._post(
            f"/aims/v1/{{account_id}}/users/{user_id}/access_keys",
            account_id=account_id,
            json_body=body if body else None,
        )

    def aims_delete_access_key(
        self,
        user_id: Annotated[str, Field(description="User ID")],
        access_key_id: Annotated[str, Field(description="Access key ID to delete")],
        account_id: Annotated[Optional[str], Field(description="Account ID")] = None,
    ) -> dict:
        """Delete access key. DELETE /aims/v1/{account_id}/users/{user_id}/access_keys/{access_key_id}"""
        return self._delete(
            f"/aims/v1/{{account_id}}/users/{user_id}/access_keys/{access_key_id}",
            account_id=account_id,
        )

    # ---- Password & MFA ----

    def aims_initiate_password_reset(
        self,
        email: Annotated[str, Field(description="User's email address")],
        return_to: Annotated[Optional[str], Field(description="URL to return to after reset")] = None,
    ) -> dict:
        """Initiate password reset. POST /aims/v1/reset_password"""
        body = {"email": email}
        if return_to:
            body["return_to"] = return_to
        return self._post("/aims/v1/reset_password", json_body=body)

    def aims_remove_mfa(
        self,
        username: Annotated[str, Field(description="User's email/username (URL-encoded automatically)")],
    ) -> dict:
        """Remove MFA device. DELETE /aims/v1/user/mfa/{username}"""
        from modules.base import url_quote
        return self._delete(f"/aims/v1/user/mfa/{url_quote(username)}")


def setup(server: FastMCP):
    mod = UsersModule()
    mod.register_tools(server)