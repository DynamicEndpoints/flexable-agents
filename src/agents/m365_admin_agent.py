import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import aiohttp
from msal import ConfidentialClientApplication
import pandas as pd

from ..core.base import Agent, Task, TaskResult, Message

logger = logging.getLogger(__name__)

class M365AdminAgent(Agent):
    """Agent for handling Microsoft 365 administrative tasks using Microsoft Graph API"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scopes: List[str] = None
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "user_management",
                "license_management",
                "group_management",
                "device_management",
                "security_management",
                "compliance_management",
                "teams_management",
                "sharepoint_management",
                "report_generation"
            ]
        )
        
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Microsoft Graph API configuration
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes or [
            "https://graph.microsoft.com/.default"
        ]
        
        # Initialize MSAL app
        self.msal_app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
        # Initialize session
        self.session = None
        self.access_token = None
        self.token_expires = None
        
        # Cache for common operations
        self.cache = {
            "users": {},
            "groups": {},
            "licenses": {},
            "devices": {}
        }
        
        # Initialize tools
        self.tools = [
            # User Management
            {
                "name": "create_user",
                "description": "Create a new user in Azure AD",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "display_name": {"type": "string"},
                        "user_principal_name": {"type": "string"},
                        "password": {"type": "string"},
                        "department": {"type": "string"}
                    },
                    "required": ["display_name", "user_principal_name", "password"]
                }
            },
            {
                "name": "get_user",
                "description": "Get user information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "update_user",
                "description": "Update user properties",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "properties": {"type": "object"}
                    },
                    "required": ["user_id", "properties"]
                }
            },
            {
                "name": "delete_user",
                "description": "Delete a user",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"}
                    },
                    "required": ["user_id"]
                }
            },
            # License Management
            {
                "name": "assign_license",
                "description": "Assign license to user",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "license_id": {"type": "string"}
                    },
                    "required": ["user_id", "license_id"]
                }
            },
            {
                "name": "remove_license",
                "description": "Remove license from user",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "license_id": {"type": "string"}
                    },
                    "required": ["user_id", "license_id"]
                }
            },
            # Group Management
            {
                "name": "create_group",
                "description": "Create a new group",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "display_name": {"type": "string"},
                        "description": {"type": "string"},
                        "group_types": {"type": "array", "items": {"type": "string"}},
                        "mail_enabled": {"type": "boolean"},
                        "security_enabled": {"type": "boolean"}
                    },
                    "required": ["display_name"]
                }
            },
            {
                "name": "add_member",
                "description": "Add member to group",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "string"},
                        "user_id": {"type": "string"}
                    },
                    "required": ["group_id", "user_id"]
                }
            },
            # Device Management
            {
                "name": "get_devices",
                "description": "Get device information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filter": {"type": "string"}
                    }
                }
            },
            {
                "name": "manage_device",
                "description": "Manage device settings",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    },
                    "required": ["device_id", "action"]
                }
            },
            # Security Management
            {
                "name": "get_security_alerts",
                "description": "Get security alerts",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filter": {"type": "string"},
                        "top": {"type": "integer"}
                    }
                }
            },
            {
                "name": "update_security_policy",
                "description": "Update security policy",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "policy_id": {"type": "string"},
                        "settings": {"type": "object"}
                    },
                    "required": ["policy_id", "settings"]
                }
            },
            # Teams Management
            {
                "name": "create_team",
                "description": "Create a new team",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "display_name": {"type": "string"},
                        "description": {"type": "string"},
                        "owners": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["display_name", "owners"]
                }
            },
            {
                "name": "add_channel",
                "description": "Add channel to team",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "team_id": {"type": "string"},
                        "display_name": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["team_id", "display_name"]
                }
            },
            # Report Generation
            {
                "name": "generate_report",
                "description": "Generate admin report",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string"},
                        "period": {"type": "string"},
                        "format": {"type": "string"}
                    },
                    "required": ["report_type"]
                }
            }
        ]
    
    async def _ensure_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expires:
            result = self.msal_app.acquire_token_silent(
                scopes=self.scopes,
                account=None
            )
            
            if not result:
                result = self.msal_app.acquire_token_for_client(
                    scopes=self.scopes
                )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.token_expires = datetime.now() + timedelta(seconds=result["expires_in"])
            else:
                raise Exception(f"Failed to acquire token: {result.get('error_description')}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Microsoft Graph API"""
        await self._ensure_token()
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        async with self.session.request(
            method=method,
            url=f"https://graph.microsoft.com/v1.0/{endpoint}",
            headers=headers,
            json=data,
            params=params
        ) as response:
            response_data = await response.json()
            if not response.ok:
                raise Exception(f"Graph API error: {response_data}")
            return response_data
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process M365 admin tasks"""
        try:
            if task.task_type == "user_management":
                output = await self._handle_user_management(task.input_data)
            elif task.task_type == "license_management":
                output = await self._handle_license_management(task.input_data)
            elif task.task_type == "group_management":
                output = await self._handle_group_management(task.input_data)
            elif task.task_type == "device_management":
                output = await self._handle_device_management(task.input_data)
            elif task.task_type == "security_management":
                output = await self._handle_security_management(task.input_data)
            elif task.task_type == "teams_management":
                output = await self._handle_teams_management(task.input_data)
            elif task.task_type == "report_generation":
                output = await self._handle_report_generation(task.input_data)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            return TaskResult(
                task_id=task.task_id,
                status="success",
                output=output,
                agent_id=self.agent_id
            )
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {str(e)}")
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
                agent_id=self.agent_id
            )
    
    async def _handle_user_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user management tasks"""
        action = data.pop("action")
        
        if action == "create_user":
            return await self._make_request("POST", "users", data=data)
        elif action == "get_user":
            return await self._make_request("GET", f"users/{data['user_id']}")
        elif action == "update_user":
            return await self._make_request(
                "PATCH",
                f"users/{data['user_id']}",
                data=data["properties"]
            )
        elif action == "delete_user":
            return await self._make_request("DELETE", f"users/{data['user_id']}")
        else:
            raise ValueError(f"Unknown user management action: {action}")
    
    async def _handle_license_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license management tasks"""
        action = data.pop("action")
        
        if action == "assign_license":
            return await self._make_request(
                "POST",
                f"users/{data['user_id']}/assignLicense",
                data={
                    "addLicenses": [{"skuId": data["license_id"]}],
                    "removeLicenses": []
                }
            )
        elif action == "remove_license":
            return await self._make_request(
                "POST",
                f"users/{data['user_id']}/assignLicense",
                data={
                    "addLicenses": [],
                    "removeLicenses": [data["license_id"]]
                }
            )
        else:
            raise ValueError(f"Unknown license management action: {action}")
    
    async def _handle_group_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle group management tasks"""
        action = data.pop("action")
        
        if action == "create_group":
            return await self._make_request("POST", "groups", data=data)
        elif action == "add_member":
            return await self._make_request(
                "POST",
                f"groups/{data['group_id']}/members/$ref",
                data={
                    "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{data['user_id']}"
                }
            )
        else:
            raise ValueError(f"Unknown group management action: {action}")
    
    async def _handle_device_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle device management tasks"""
        action = data.pop("action")
        
        if action == "get_devices":
            return await self._make_request(
                "GET",
                "devices",
                params={"$filter": data.get("filter")}
            )
        elif action == "manage_device":
            return await self._make_request(
                "POST",
                f"devices/{data['device_id']}/{data['action']}",
                data=data.get("settings")
            )
        else:
            raise ValueError(f"Unknown device management action: {action}")
    
    async def _handle_security_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle security management tasks"""
        action = data.pop("action")
        
        if action == "get_security_alerts":
            return await self._make_request(
                "GET",
                "security/alerts",
                params={
                    "$filter": data.get("filter"),
                    "$top": data.get("top", 10)
                }
            )
        elif action == "update_security_policy":
            return await self._make_request(
                "PATCH",
                f"security/securityPolicies/{data['policy_id']}",
                data=data["settings"]
            )
        else:
            raise ValueError(f"Unknown security management action: {action}")
    
    async def _handle_teams_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Teams management tasks"""
        action = data.pop("action")
        
        if action == "create_team":
            return await self._make_request("POST", "teams", data=data)
        elif action == "add_channel":
            return await self._make_request(
                "POST",
                f"teams/{data['team_id']}/channels",
                data={
                    "displayName": data["display_name"],
                    "description": data.get("description", "")
                }
            )
        else:
            raise ValueError(f"Unknown Teams management action: {action}")
    
    async def _handle_report_generation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report generation tasks"""
        report_type = data["report_type"]
        period = data.get("period", "D7")
        format = data.get("format", "json")
        
        response = await self._make_request(
            "GET",
            f"reports/{report_type}({period})",
            params={"$format": format}
        )
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.work_dir / f"{report_type}_{timestamp}.{format}"
        
        if format == "json":
            with open(report_file, "w") as f:
                json.dump(response, f, indent=2)
        elif format == "csv":
            pd.DataFrame(response).to_csv(report_file, index=False)
        
        return {
            "report_type": report_type,
            "period": period,
            "format": format,
            "file_path": str(report_file)
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
