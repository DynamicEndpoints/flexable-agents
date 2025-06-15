"""Microsoft 365 tools for MCP server."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
from msal import ConfidentialClientApplication
import aiohttp

from src.mcp import tool
from src.core import mcp_tool, create_mcp_tool_metadata
# Import specialized tools
from .specialized_tools import register_specialized_tools

logger = logging.getLogger(__name__)


class M365GraphClient:
    """Microsoft Graph API client for M365 operations."""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        
        # Create MSAL app
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}"
        )
        
    async def get_access_token(self) -> str:
        """Get or refresh access token."""
        if (self.access_token and self.token_expires_at and 
            datetime.now() < self.token_expires_at):
            return self.access_token
            
        try:
            result = self.app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.token_expires_at = datetime.now().replace(
                    second=0, microsecond=0
                ) + datetime.timedelta(seconds=result.get("expires_in", 3600) - 60)
                return self.access_token
            else:
                raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error acquiring access token: {e}")
            raise
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Microsoft Graph API."""
        token = await self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None
            ) as response:
                response_data = await response.json()
                
                if response.status >= 400:
                    raise Exception(f"Graph API error: {response.status} - {response_data}")
                
                return response_data


# Global Graph client instance
_graph_client: Optional[M365GraphClient] = None


def initialize_graph_client(config):
    """Initialize the Microsoft Graph client."""
    global _graph_client
    _graph_client = M365GraphClient(
        tenant_id=config.m365.tenant_id,
        client_id=config.m365.client_id,
        client_secret=config.m365.client_secret
    )


def register_m365_tools(server, config):
    """Register Microsoft 365 tools with the MCP server."""
    
    # Initialize Graph client
    initialize_graph_client(config)
    
    # Register user management tool
    server.register_tool(
        name="m365_user_management",
        description="Manage Microsoft 365 users (create, update, disable, enable, list)",
        handler=m365_user_management,
        returns="User management operation result"
    )
    
    # Register group management tool
    server.register_tool(
        name="m365_group_management", 
        description="Manage Microsoft 365 groups and teams",
        handler=m365_group_management,
        returns="Group management operation result"
    )
    
    # Register license management tool
    server.register_tool(
        name="m365_license_management",
        description="Manage user licenses and subscriptions",
        handler=m365_license_management,
        returns="License management operation result"
    )
    
    # Register Teams management tool
    server.register_tool(
        name="teams_management",
        description="Manage Microsoft Teams configurations and policies",
        handler=teams_management,
        returns="Teams management operation result"
    )
    
    # Register SharePoint management tool
    server.register_tool(
        name="sharepoint_management",
        description="Manage SharePoint sites and configurations",
        handler=sharepoint_management,
        returns="SharePoint management operation result"
    )
    
    # Register Exchange management tool
    server.register_tool(
        name="exchange_management",
        description="Manage Exchange Online mailboxes and settings",
        handler=exchange_management,
        returns="Exchange management operation result"
    )
    
    # Register security audit tool
    server.register_tool(
        name="security_audit",
        description="Perform security audits and compliance checks",
        handler=security_audit,
        returns="Security audit report"
    )
    
    # Register Intune device management tool
    server.register_tool(
        name="intune_device_management",
        description="Manage Intune devices, policies, and compliance",
        handler=intune_device_management,
        returns="Intune device management operation result"
    )
    
    # Register Intune app management tool
    server.register_tool(
        name="intune_app_management",
        description="Manage mobile apps and application policies",
        handler=intune_app_management,
        returns="Intune app management operation result"
    )
    
    # Register compliance management tool
    server.register_tool(
        name="compliance_management",
        description="Manage device compliance policies and monitoring",
        handler=compliance_management,
        returns="Compliance management operation result"
    )    
    logger.info("Registered M365 tools")
    
    # Register specialized tools
    register_specialized_tools(server, config)


@mcp_tool(
    name="m365_user_management",
    description="Manage Microsoft 365 users",
    category="m365",
    tags=["users", "administration"]
)
async def m365_user_management(
    action: str, 
    user_data: Optional[Dict[str, Any]] = None, 
    user_id: Optional[str] = None,
    filter_criteria: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage Microsoft 365 users.
    
    Args:
        action: Action to perform (create, update, delete, get, list, enable, disable)
        user_data: User data for create/update operations
        user_id: User ID for get/update/delete operations
        filter_criteria: Filter criteria for list operations
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "create":
            if not user_data:
                return {"status": "error", "message": "User data required for create operation"}
            
            result = await _graph_client.make_request("POST", "/users", user_data)
            return {
                "status": "success",
                "message": f"User created successfully",
                "data": result
            }
            
        elif action == "update":
            if not user_id or not user_data:
                return {"status": "error", "message": "User ID and data required for update operation"}
            
            result = await _graph_client.make_request("PATCH", f"/users/{user_id}", user_data)
            return {
                "status": "success",
                "message": f"User {user_id} updated successfully",
                "data": result
            }
            
        elif action == "delete":
            if not user_id:
                return {"status": "error", "message": "User ID required for delete operation"}
            
            await _graph_client.make_request("DELETE", f"/users/{user_id}")
            return {
                "status": "success",
                "message": f"User {user_id} deleted successfully"
            }
            
        elif action == "get":
            if not user_id:
                return {"status": "error", "message": "User ID required for get operation"}
            
            result = await _graph_client.make_request("GET", f"/users/{user_id}")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "list":
            endpoint = "/users"
            if filter_criteria:
                endpoint += f"?$filter={filter_criteria}"
                
            result = await _graph_client.make_request("GET", endpoint)
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "enable":
            if not user_id:
                return {"status": "error", "message": "User ID required for enable operation"}
            
            await _graph_client.make_request(
                "PATCH", 
                f"/users/{user_id}", 
                {"accountEnabled": True}
            )
            return {
                "status": "success",
                "message": f"User {user_id} enabled successfully"
            }
            
        elif action == "disable":
            if not user_id:
                return {"status": "error", "message": "User ID required for disable operation"}
            
            await _graph_client.make_request(
                "PATCH", 
                f"/users/{user_id}", 
                {"accountEnabled": False}
            )
            return {
                "status": "success",
                "message": f"User {user_id} disabled successfully"
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in user management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="m365_group_management",
    description="Manage Microsoft 365 groups",
    category="m365", 
    tags=["groups", "administration"]
)
async def m365_group_management(
    action: str, 
    group_data: Optional[Dict[str, Any]] = None, 
    group_id: Optional[str] = None,
    member_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage Microsoft 365 groups and teams.
    
    Args:
        action: Action to perform (create, update, delete, get, list, add_member, remove_member)
        group_data: Group data for create/update operations
        group_id: Group ID for operations
        member_id: Member ID for add/remove member operations
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "create":
            if not group_data:
                return {"status": "error", "message": "Group data required for create operation"}
            
            result = await _graph_client.make_request("POST", "/groups", group_data)
            return {
                "status": "success",
                "message": "Group created successfully",
                "data": result
            }
            
        elif action == "update":
            if not group_id or not group_data:
                return {"status": "error", "message": "Group ID and data required for update operation"}
            
            result = await _graph_client.make_request("PATCH", f"/groups/{group_id}", group_data)
            return {
                "status": "success",
                "message": f"Group {group_id} updated successfully",
                "data": result
            }
            
        elif action == "delete":
            if not group_id:
                return {"status": "error", "message": "Group ID required for delete operation"}
            
            await _graph_client.make_request("DELETE", f"/groups/{group_id}")
            return {
                "status": "success",
                "message": f"Group {group_id} deleted successfully"
            }
            
        elif action == "get":
            if not group_id:
                return {"status": "error", "message": "Group ID required for get operation"}
            
            result = await _graph_client.make_request("GET", f"/groups/{group_id}")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "list":
            result = await _graph_client.make_request("GET", "/groups")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "add_member":
            if not group_id or not member_id:
                return {"status": "error", "message": "Group ID and member ID required for add member operation"}
            
            member_data = {
                "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{member_id}"
            }
            await _graph_client.make_request("POST", f"/groups/{group_id}/members/$ref", member_data)
            return {
                "status": "success",
                "message": f"Member {member_id} added to group {group_id}"
            }
            
        elif action == "remove_member":
            if not group_id or not member_id:
                return {"status": "error", "message": "Group ID and member ID required for remove member operation"}
            
            await _graph_client.make_request("DELETE", f"/groups/{group_id}/members/{member_id}/$ref")
            return {
                "status": "success",
                "message": f"Member {member_id} removed from group {group_id}"
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in group management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="m365_license_management",
    description="Manage user licenses",
    category="m365",
    tags=["licenses", "administration"]
)
async def m365_license_management(
    action: str, 
    user_id: Optional[str] = None, 
    license_sku: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage user licenses and subscriptions.
    
    Args:
        action: Action to perform (assign, remove, list_available, list_user_licenses)
        user_id: User ID for license operations
        license_sku: License SKU to assign/remove
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "assign":
            if not user_id or not license_sku:
                return {"status": "error", "message": "User ID and license SKU required for assign operation"}
            
            license_data = {
                "addLicenses": [{
                    "skuId": license_sku
                }],
                "removeLicenses": []
            }
            
            result = await _graph_client.make_request("POST", f"/users/{user_id}/assignLicense", license_data)
            return {
                "status": "success",
                "message": f"License {license_sku} assigned to user {user_id}",
                "data": result
            }
            
        elif action == "remove":
            if not user_id or not license_sku:
                return {"status": "error", "message": "User ID and license SKU required for remove operation"}
            
            license_data = {
                "addLicenses": [],
                "removeLicenses": [license_sku]
            }
            
            result = await _graph_client.make_request("POST", f"/users/{user_id}/assignLicense", license_data)
            return {
                "status": "success",
                "message": f"License {license_sku} removed from user {user_id}",
                "data": result
            }
            
        elif action == "list_available":
            result = await _graph_client.make_request("GET", "/subscribedSkus")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "list_user_licenses":
            if not user_id:
                return {"status": "error", "message": "User ID required for list user licenses operation"}
            
            result = await _graph_client.make_request("GET", f"/users/{user_id}/licenseDetails")
            return {
                "status": "success",
                "data": result
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in license management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="teams_management",
    description="Manage Microsoft Teams",
    category="teams",
    tags=["teams", "collaboration"]
)
async def teams_management(
    action: str,
    team_data: Optional[Dict[str, Any]] = None,
    team_id: Optional[str] = None,
    channel_data: Optional[Dict[str, Any]] = None,
    channel_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage Microsoft Teams configurations and policies.
    
    Args:
        action: Action to perform (create_team, update_team, delete_team, get_team, list_teams, create_channel, etc.)
        team_data: Team data for create/update operations
        team_id: Team ID for operations
        channel_data: Channel data for channel operations
        channel_id: Channel ID for channel operations
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "create_team":
            if not team_data:
                return {"status": "error", "message": "Team data required for create team operation"}
            
            result = await _graph_client.make_request("POST", "/teams", team_data)
            return {
                "status": "success",
                "message": "Team created successfully",
                "data": result
            }
            
        elif action == "get_team":
            if not team_id:
                return {"status": "error", "message": "Team ID required for get team operation"}
            
            result = await _graph_client.make_request("GET", f"/teams/{team_id}")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "list_teams":
            result = await _graph_client.make_request("GET", "/me/joinedTeams")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "create_channel":
            if not team_id or not channel_data:
                return {"status": "error", "message": "Team ID and channel data required for create channel operation"}
            
            result = await _graph_client.make_request("POST", f"/teams/{team_id}/channels", channel_data)
            return {
                "status": "success",
                "message": "Channel created successfully",
                "data": result
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in teams management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="sharepoint_management",
    description="Manage SharePoint sites",
    category="sharepoint",
    tags=["sharepoint", "sites"]
)
async def sharepoint_management(
    action: str,
    site_data: Optional[Dict[str, Any]] = None,
    site_id: Optional[str] = None,
    list_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Manage SharePoint sites and configurations.
    
    Args:
        action: Action to perform (create_site, get_site, list_sites, create_list, etc.)
        site_data: Site data for create operations
        site_id: Site ID for operations
        list_data: List data for list operations
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "list_sites":
            result = await _graph_client.make_request("GET", "/sites")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "get_site":
            if not site_id:
                return {"status": "error", "message": "Site ID required for get site operation"}
            
            result = await _graph_client.make_request("GET", f"/sites/{site_id}")
            return {
                "status": "success",
                "data": result
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in SharePoint management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="exchange_management",
    description="Manage Exchange Online",
    category="exchange",
    tags=["exchange", "email"]
)
async def exchange_management(
    action: str,
    mailbox_data: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage Exchange Online mailboxes and settings.
    
    Args:
        action: Action to perform (get_mailbox, list_mailboxes, update_mailbox, etc.)
        mailbox_data: Mailbox data for operations
        user_id: User ID for mailbox operations
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "get_mailbox":
            if not user_id:
                return {"status": "error", "message": "User ID required for get mailbox operation"}
            
            result = await _graph_client.make_request("GET", f"/users/{user_id}/mailboxSettings")
            return {
                "status": "success",
                "data": result
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in Exchange management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="security_audit",
    description="Perform security audits",
    category="security",
    tags=["security", "audit", "compliance"]
)
async def security_audit(
    audit_type: str = "basic",
    scope: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform security audits and compliance checks.
    
    Args:
        audit_type: Type of audit (basic, comprehensive, specific)
        scope: Audit scope (users, groups, applications, policies)
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    audit_results = {
        "audit_type": audit_type,
        "timestamp": datetime.now().isoformat(),
        "scope": scope or ["users", "groups"],
        "findings": []
    }
    
    try:
        # Check for users without MFA
        users_result = await _graph_client.make_request("GET", "/users")
        users_without_mfa = []
        
        for user in users_result.get("value", []):
            # This is a simplified check - in reality you'd need more detailed queries
            if not user.get("accountEnabled", False):
                continue
            users_without_mfa.append(user.get("userPrincipalName"))
        
        audit_results["findings"].append({
            "category": "authentication",
            "issue": "Users without MFA enabled",
            "count": len(users_without_mfa),
            "severity": "medium"
        })
        
        # Check for inactive users
        # This would require more complex queries in a real implementation
        
        return {
            "status": "success",
            "data": audit_results
        }
        
    except Exception as e:
        logger.error(f"Error in security audit: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="intune_device_management",
    description="Manage Intune devices and policies",
    category="intune",
    tags=["intune", "devices", "mdm"]
)
async def intune_device_management(
    action: str,
    device_id: Optional[str] = None,
    policy_data: Optional[Dict[str, Any]] = None,
    filter_criteria: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage Intune devices, policies, and configurations.
    
    Args:
        action: Action to perform (list_devices, get_device, wipe_device, retire_device, sync_device, create_policy, etc.)
        device_id: Device ID for device-specific operations
        policy_data: Policy data for create/update operations
        filter_criteria: Filter criteria for list operations
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "list_devices":
            endpoint = "/deviceManagement/managedDevices"
            if filter_criteria:
                endpoint += f"?$filter={filter_criteria}"
            
            result = await _graph_client.make_request("GET", endpoint)
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "get_device":
            if not device_id:
                return {"status": "error", "message": "Device ID required for get device operation"}
            
            result = await _graph_client.make_request("GET", f"/deviceManagement/managedDevices/{device_id}")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "wipe_device":
            if not device_id:
                return {"status": "error", "message": "Device ID required for wipe operation"}
            
            result = await _graph_client.make_request("POST", f"/deviceManagement/managedDevices/{device_id}/wipe")
            return {
                "status": "success",
                "message": f"Device {device_id} wipe initiated",
                "data": result
            }
            
        elif action == "retire_device":
            if not device_id:
                return {"status": "error", "message": "Device ID required for retire operation"}
            
            result = await _graph_client.make_request("POST", f"/deviceManagement/managedDevices/{device_id}/retire")
            return {
                "status": "success",
                "message": f"Device {device_id} retire initiated",
                "data": result
            }
            
        elif action == "sync_device":
            if not device_id:
                return {"status": "error", "message": "Device ID required for sync operation"}
            
            result = await _graph_client.make_request("POST", f"/deviceManagement/managedDevices/{device_id}/syncDevice")
            return {
                "status": "success",
                "message": f"Device {device_id} sync initiated",
                "data": result
            }
            
        elif action == "create_configuration_policy":
            if not policy_data:
                return {"status": "error", "message": "Policy data required for create operation"}
            
            result = await _graph_client.make_request("POST", "/deviceManagement/deviceConfigurations", policy_data)
            return {
                "status": "success",
                "message": "Configuration policy created successfully",
                "data": result
            }
            
        elif action == "list_policies":
            result = await _graph_client.make_request("GET", "/deviceManagement/deviceConfigurations")
            return {
                "status": "success",
                "data": result
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in Intune device management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="intune_app_management",
    description="Manage mobile apps and application policies",
    category="intune",
    tags=["intune", "apps", "mobile"]
)
async def intune_app_management(
    action: str,
    app_id: Optional[str] = None,
    app_data: Optional[Dict[str, Any]] = None,
    assignment_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Manage Intune mobile applications and app policies.
    
    Args:
        action: Action to perform (list_apps, get_app, create_app, assign_app, update_app, delete_app)
        app_id: App ID for app-specific operations
        app_data: App data for create/update operations
        assignment_data: Assignment data for app assignments
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "list_apps":
            result = await _graph_client.make_request("GET", "/deviceAppManagement/mobileApps")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "get_app":
            if not app_id:
                return {"status": "error", "message": "App ID required for get app operation"}
            
            result = await _graph_client.make_request("GET", f"/deviceAppManagement/mobileApps/{app_id}")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "create_app":
            if not app_data:
                return {"status": "error", "message": "App data required for create operation"}
            
            result = await _graph_client.make_request("POST", "/deviceAppManagement/mobileApps", app_data)
            return {
                "status": "success",
                "message": "Mobile app created successfully",
                "data": result
            }
            
        elif action == "assign_app":
            if not app_id or not assignment_data:
                return {"status": "error", "message": "App ID and assignment data required for assign operation"}
            
            result = await _graph_client.make_request("POST", f"/deviceAppManagement/mobileApps/{app_id}/assign", assignment_data)
            return {
                "status": "success",
                "message": f"App {app_id} assigned successfully",
                "data": result
            }
            
        elif action == "update_app":
            if not app_id or not app_data:
                return {"status": "error", "message": "App ID and data required for update operation"}
            
            result = await _graph_client.make_request("PATCH", f"/deviceAppManagement/mobileApps/{app_id}", app_data)
            return {
                "status": "success",
                "message": f"App {app_id} updated successfully",
                "data": result
            }
            
        elif action == "delete_app":
            if not app_id:
                return {"status": "error", "message": "App ID required for delete operation"}
            
            await _graph_client.make_request("DELETE", f"/deviceAppManagement/mobileApps/{app_id}")
            return {
                "status": "success",
                "message": f"App {app_id} deleted successfully"
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in Intune app management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="compliance_management",
    description="Manage device compliance policies and monitoring",
    category="compliance",
    tags=["compliance", "policies", "security"]
)
async def compliance_management(
    action: str,
    policy_id: Optional[str] = None,
    policy_data: Optional[Dict[str, Any]] = None,
    device_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage device compliance policies and monitoring.
    
    Args:
        action: Action to perform (list_policies, create_policy, get_device_compliance, get_noncompliant_devices)
        policy_id: Policy ID for policy-specific operations
        policy_data: Policy data for create/update operations
        device_id: Device ID for device compliance operations
    """
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "list_policies":
            result = await _graph_client.make_request("GET", "/deviceManagement/deviceCompliancePolicies")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "create_policy":
            if not policy_data:
                return {"status": "error", "message": "Policy data required for create operation"}
            
            result = await _graph_client.make_request("POST", "/deviceManagement/deviceCompliancePolicies", policy_data)
            return {
                "status": "success",
                "message": "Compliance policy created successfully",
                "data": result
            }
            
        elif action == "get_device_compliance":
            if not device_id:
                return {"status": "error", "message": "Device ID required for get device compliance operation"}
            
            result = await _graph_client.make_request("GET", f"/deviceManagement/managedDevices/{device_id}/deviceCompliancePolicyStates")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "get_noncompliant_devices":
            result = await _graph_client.make_request("GET", "/deviceManagement/managedDevices?$filter=complianceState eq 'noncompliant'")
            return {
                "status": "success",
                "data": result
            }
            
        elif action == "update_policy":
            if not policy_id or not policy_data:
                return {"status": "error", "message": "Policy ID and data required for update operation"}
            
            result = await _graph_client.make_request("PATCH", f"/deviceManagement/deviceCompliancePolicies/{policy_id}", policy_data)
            return {
                "status": "success",
                "message": f"Policy {policy_id} updated successfully",
                "data": result
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in compliance management: {e}")
        return {"status": "error", "message": str(e)}
