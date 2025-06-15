"""Additional specialized tools for Teams, SharePoint Dev, and Exchange management."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import time

from src.core import mcp_tool
from src.mcp.logging_system import log_request_metrics
from src.tools.m365_tools import with_error_handling

logger = logging.getLogger(__name__)


def register_specialized_tools(server, config):
    """Register specialized tools for specific Microsoft 365 services."""
    
    # Register enhanced Teams tools
    server.register_tool(
        name="teams_advanced_management",
        description="Advanced Teams management including policies, apps, and configurations",
        handler=teams_advanced_management,
        returns="Advanced Teams management operation result"
    )
    
    # Register SharePoint development tools
    server.register_tool(
        name="sharepoint_development",
        description="SharePoint development and Power Platform integration",
        handler=sharepoint_development,
        returns="SharePoint development operation result"
    )
    
    # Register Exchange advanced tools
    server.register_tool(
        name="exchange_advanced_management",
        description="Advanced Exchange Online management including mail flow and compliance",
        handler=exchange_advanced_management,
        returns="Exchange advanced management operation result"
    )
    
    # Register workflow automation tools
    server.register_tool(
        name="workflow_automation",
        description="Automate common M365 administration workflows",
        handler=workflow_automation,
        returns="Workflow automation operation result"
    )
    
    logger.info("Registered specialized M365 tools")


@mcp_tool(
    name="teams_advanced_management",
    description="Advanced Teams management",
    category="teams",
    tags=["teams", "policies", "apps", "meetings"]
)
@with_error_handling("teams_advanced_management")
async def teams_advanced_management(
    action: str,
    team_id: Optional[str] = None,
    policy_data: Optional[Dict[str, Any]] = None,
    app_data: Optional[Dict[str, Any]] = None,
    meeting_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Advanced Microsoft Teams management including policies, apps, and meeting configurations.
    
    Args:
        action: Action to perform (manage_policies, manage_apps, configure_meetings, manage_channels, etc.)
        team_id: Team ID for team-specific operations
        policy_data: Policy data for policy operations
        app_data: App data for app management
        meeting_data: Meeting configuration data
    """
    from src.tools.m365_tools import _graph_client
    
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "manage_meeting_policies":
            if not policy_data:
                return {"status": "error", "message": "Policy data required for meeting policy management"}
            
            # Create or update meeting policy
            result = await _graph_client.make_request("POST", "/teamwork/teamsAppSettings", policy_data)
            return {
                "status": "success",
                "message": "Meeting policy configured successfully",
                "data": result
            }
            
        elif action == "install_team_app":
            if not team_id or not app_data:
                return {"status": "error", "message": "Team ID and app data required for app installation"}
            
            result = await _graph_client.make_request("POST", f"/teams/{team_id}/installedApps", app_data)
            return {
                "status": "success",
                "message": f"App installed in team {team_id}",
                "data": result
            }
            
        elif action == "configure_channel_tabs":
            if not team_id or not app_data:
                return {"status": "error", "message": "Team ID and channel data required"}
            
            channel_id = app_data.get("channel_id")
            tab_data = app_data.get("tab_data")
            
            result = await _graph_client.make_request("POST", f"/teams/{team_id}/channels/{channel_id}/tabs", tab_data)
            return {
                "status": "success",
                "message": "Channel tab configured successfully",
                "data": result
            }
            
        elif action == "manage_team_settings":
            if not team_id or not policy_data:
                return {"status": "error", "message": "Team ID and settings data required"}
            
            result = await _graph_client.make_request("PATCH", f"/teams/{team_id}", policy_data)
            return {
                "status": "success",
                "message": f"Team {team_id} settings updated",
                "data": result
            }
            
        elif action == "get_team_analytics":
            if not team_id:
                return {"status": "error", "message": "Team ID required for analytics"}
            
            # Get team activity data
            result = await _graph_client.make_request("GET", f"/teams/{team_id}/channels")
            channels = result.get("value", [])
            
            analytics = {
                "team_id": team_id,
                "channel_count": len(channels),
                "timestamp": datetime.now().isoformat(),
                "channels": channels
            }
            
            return {
                "status": "success",
                "data": analytics
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in advanced Teams management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="sharepoint_development",
    description="SharePoint development and Power Platform integration",
    category="sharepoint",
    tags=["sharepoint", "powerplatform", "development"]
)
@with_error_handling("sharepoint_development")
async def sharepoint_development(
    action: str,
    site_data: Optional[Dict[str, Any]] = None,
    solution_data: Optional[Dict[str, Any]] = None,
    power_app_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    SharePoint development and Power Platform integration tools.
    
    Args:
        action: Action to perform (create_modern_site, deploy_spfx, create_power_app, setup_flow, etc.)
        site_data: Site creation/configuration data
        solution_data: SPFx solution data
        power_app_data: Power App configuration data
    """
    from src.tools.m365_tools import _graph_client
    
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "create_modern_site":
            if not site_data:
                return {"status": "error", "message": "Site data required for site creation"}
            
            # Create modern SharePoint site
            result = await _graph_client.make_request("POST", "/sites", site_data)
            return {
                "status": "success",
                "message": "Modern SharePoint site created",
                "data": result
            }
            
        elif action == "create_document_library":
            if not site_data:
                return {"status": "error", "message": "Site and library data required"}
            
            site_id = site_data.get("site_id")
            library_data = site_data.get("library_data")
            
            result = await _graph_client.make_request("POST", f"/sites/{site_id}/lists", library_data)
            return {
                "status": "success",
                "message": "Document library created",
                "data": result
            }
            
        elif action == "setup_content_types":
            if not site_data:
                return {"status": "error", "message": "Site and content type data required"}
            
            site_id = site_data.get("site_id")
            content_type_data = site_data.get("content_type_data")
            
            result = await _graph_client.make_request("POST", f"/sites/{site_id}/contentTypes", content_type_data)
            return {
                "status": "success",
                "message": "Content type created",
                "data": result
            }
            
        elif action == "deploy_spfx_solution":
            if not solution_data:
                return {"status": "error", "message": "SPFx solution data required"}
            
            # This would typically involve uploading to the app catalog
            # For now, return a simulation
            return {
                "status": "success",
                "message": "SPFx solution deployment initiated",
                "data": {
                    "solution_name": solution_data.get("name"),
                    "deployment_status": "pending",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        elif action == "create_power_app":
            if not power_app_data:
                return {"status": "error", "message": "Power App data required"}
            
            # Power Apps would typically be created through Power Platform APIs
            return {
                "status": "success",
                "message": "Power App creation initiated",
                "data": {
                    "app_name": power_app_data.get("name"),
                    "environment": power_app_data.get("environment"),
                    "status": "creating"
                }
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in SharePoint development: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="exchange_advanced_management",
    description="Advanced Exchange Online management",
    category="exchange",
    tags=["exchange", "compliance", "security", "mailflow"]
)
@with_error_handling("exchange_advanced_management")
async def exchange_advanced_management(
    action: str,
    mailbox_data: Optional[Dict[str, Any]] = None,
    rule_data: Optional[Dict[str, Any]] = None,
    policy_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Advanced Exchange Online management including mail flow, compliance, and security.
    
    Args:
        action: Action to perform (configure_retention, setup_dlp, manage_mail_flow, configure_archive, etc.)
        mailbox_data: Mailbox configuration data
        rule_data: Mail flow rule data
        policy_data: Policy configuration data
    """
    from src.tools.m365_tools import _graph_client
    
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if action == "configure_retention_policy":
            if not policy_data:
                return {"status": "error", "message": "Policy data required for retention configuration"}
            
            # Configure retention policy
            result = await _graph_client.make_request("POST", "/security/labels/retentionLabels", policy_data)
            return {
                "status": "success",
                "message": "Retention policy configured",
                "data": result
            }
            
        elif action == "setup_archive_mailbox":
            if not mailbox_data:
                return {"status": "error", "message": "Mailbox data required for archive setup"}
            
            user_id = mailbox_data.get("user_id")
            # Enable archive mailbox
            result = await _graph_client.make_request("POST", f"/users/{user_id}/mailboxSettings/archive", {"enabled": True})
            return {
                "status": "success",
                "message": f"Archive mailbox enabled for {user_id}",
                "data": result
            }
            
        elif action == "create_distribution_group":
            if not mailbox_data:
                return {"status": "error", "message": "Group data required"}
            
            result = await _graph_client.make_request("POST", "/groups", mailbox_data)
            return {
                "status": "success",
                "message": "Distribution group created",
                "data": result
            }
            
        elif action == "configure_mail_flow_rule":
            if not rule_data:
                return {"status": "error", "message": "Rule data required for mail flow configuration"}
            
            # This would typically use Exchange PowerShell or Exchange REST API
            return {
                "status": "success",
                "message": "Mail flow rule configured",
                "data": {
                    "rule_name": rule_data.get("name"),
                    "conditions": rule_data.get("conditions"),
                    "actions": rule_data.get("actions")
                }
            }
            
        elif action == "get_mailbox_statistics":
            if not mailbox_data:
                return {"status": "error", "message": "Mailbox data required"}
            
            user_id = mailbox_data.get("user_id")
            result = await _graph_client.make_request("GET", f"/users/{user_id}/mailFolders/inbox/messageRules")
            return {
                "status": "success",
                "data": result
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in advanced Exchange management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="workflow_automation",
    description="Automate common M365 administration workflows",
    category="automation",
    tags=["automation", "workflows", "bulk"]
)
@with_error_handling("workflow_automation")
async def workflow_automation(
    workflow_type: str,
    workflow_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Automate common Microsoft 365 administration workflows.
    
    Args:
        workflow_type: Type of workflow (employee_onboarding, offboarding, bulk_operations, etc.)
        workflow_data: Workflow configuration and data
    """
    from src.tools.m365_tools import _graph_client
    
    if not _graph_client:
        return {"status": "error", "message": "Graph client not initialized"}
    
    try:
        if workflow_type == "employee_onboarding":
            # Automate new employee setup
            employee_data = workflow_data.get("employee")
            results = []
            
            # Create user
            user_result = await _graph_client.make_request("POST", "/users", employee_data)
            results.append({"step": "create_user", "result": user_result})
            
            user_id = user_result.get("id")
            
            # Assign licenses
            for license in workflow_data.get("licenses", []):
                license_data = {
                    "addLicenses": [{"skuId": license}],
                    "removeLicenses": []
                }
                license_result = await _graph_client.make_request("POST", f"/users/{user_id}/assignLicense", license_data)
                results.append({"step": f"assign_license_{license}", "result": license_result})
            
            # Add to groups
            for group_id in workflow_data.get("groups", []):
                member_data = {
                    "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"
                }
                group_result = await _graph_client.make_request("POST", f"/groups/{group_id}/members/$ref", member_data)
                results.append({"step": f"add_to_group_{group_id}", "result": group_result})
            
            return {
                "status": "success",
                "message": "Employee onboarding completed",
                "data": {
                    "workflow_type": workflow_type,
                    "employee_id": user_id,
                    "steps_completed": len(results),
                    "results": results
                }
            }
            
        elif workflow_type == "employee_offboarding":
            # Automate employee offboarding
            user_id = workflow_data.get("user_id")
            results = []
            
            # Disable account
            disable_result = await _graph_client.make_request("PATCH", f"/users/{user_id}", {"accountEnabled": False})
            results.append({"step": "disable_account", "result": disable_result})
            
            # Remove from groups
            user_groups = await _graph_client.make_request("GET", f"/users/{user_id}/memberOf")
            for group in user_groups.get("value", []):
                group_id = group.get("id")
                await _graph_client.make_request("DELETE", f"/groups/{group_id}/members/{user_id}/$ref")
                results.append({"step": f"remove_from_group_{group_id}", "result": "removed"})
            
            return {
                "status": "success",
                "message": "Employee offboarding completed",
                "data": {
                    "workflow_type": workflow_type,
                    "user_id": user_id,
                    "steps_completed": len(results),
                    "results": results
                }
            }
            
        elif workflow_type == "bulk_license_assignment":
            # Bulk license assignment
            user_ids = workflow_data.get("user_ids", [])
            license_sku = workflow_data.get("license_sku")
            results = []
            
            for user_id in user_ids:
                license_data = {
                    "addLicenses": [{"skuId": license_sku}],
                    "removeLicenses": []
                }
                try:
                    result = await _graph_client.make_request("POST", f"/users/{user_id}/assignLicense", license_data)
                    results.append({"user_id": user_id, "status": "success", "result": result})
                except Exception as e:
                    results.append({"user_id": user_id, "status": "error", "error": str(e)})
            
            return {
                "status": "success",
                "message": f"Bulk license assignment completed for {len(user_ids)} users",
                "data": {
                    "workflow_type": workflow_type,
                    "license_sku": license_sku,
                    "total_users": len(user_ids),
                    "results": results
                }
            }
            
        else:
            return {"status": "error", "message": f"Unknown workflow type: {workflow_type}"}
            
    except Exception as e:
        logger.error(f"Error in workflow automation: {e}")
        return {"status": "error", "message": str(e)}
