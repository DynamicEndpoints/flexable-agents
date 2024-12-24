import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import aiohttp
from datetime import datetime, timedelta

from ..core.base import Agent, Task, TaskResult

logger = logging.getLogger(__name__)

class TeamsAgent(Agent):
    """Agent for managing Microsoft Teams configurations and policies"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        graph_client: Any  # Microsoft Graph client from m365_admin_agent
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "team_management",
                "channel_management",
                "meeting_management",
                "policy_management",
                "app_management",
                "chat_management"
            ]
        )
        
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.graph_client = graph_client
        
        self.tools = [
            # Team Management
            {
                "name": "manage_team",
                "description": "Manage Teams team",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "team_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            },
            # Channel Management
            {
                "name": "manage_channel",
                "description": "Manage Teams channels",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "team_id": {"type": "string"},
                        "channel_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            },
            # Meeting Management
            {
                "name": "manage_meeting",
                "description": "Manage Teams meetings",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "meeting_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            }
        ]
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process Teams management tasks"""
        try:
            if task.task_type == "team_management":
                output = await self._handle_team_management(task.input_data)
            elif task.task_type == "channel_management":
                output = await self._handle_channel_management(task.input_data)
            elif task.task_type == "meeting_management":
                output = await self._handle_meeting_management(task.input_data)
            elif task.task_type == "policy_management":
                output = await self._handle_policy_management(task.input_data)
            elif task.task_type == "app_management":
                output = await self._handle_app_management(task.input_data)
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
    
    async def _handle_team_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle team management tasks"""
        action = data.get("action")
        team_id = data.get("team_id")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                "teams",
                data=data.get("settings", {})
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"teams/{team_id}",
                data=data.get("settings", {})
            )
        elif action == "delete":
            return await self.graph_client._make_request(
                "DELETE",
                f"teams/{team_id}"
            )
        elif action == "archive":
            return await self.graph_client._make_request(
                "POST",
                f"teams/{team_id}/archive",
                data=data.get("settings", {})
            )
        elif action == "unarchive":
            return await self.graph_client._make_request(
                "POST",
                f"teams/{team_id}/unarchive"
            )
        elif action == "clone":
            return await self.graph_client._make_request(
                "POST",
                f"teams/{team_id}/clone",
                data=data.get("settings", {})
            )
        else:
            raise ValueError(f"Unknown team management action: {action}")
    
    async def _handle_channel_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle channel management tasks"""
        action = data.get("action")
        team_id = data.get("team_id")
        channel_id = data.get("channel_id")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                f"teams/{team_id}/channels",
                data=data.get("settings", {})
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"teams/{team_id}/channels/{channel_id}",
                data=data.get("settings", {})
            )
        elif action == "delete":
            return await self.graph_client._make_request(
                "DELETE",
                f"teams/{team_id}/channels/{channel_id}"
            )
        elif action == "list_members":
            return await self.graph_client._make_request(
                "GET",
                f"teams/{team_id}/channels/{channel_id}/members"
            )
        elif action == "add_member":
            return await self.graph_client._make_request(
                "POST",
                f"teams/{team_id}/channels/{channel_id}/members",
                data=data.get("settings", {})
            )
        else:
            raise ValueError(f"Unknown channel management action: {action}")
    
    async def _handle_meeting_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle meeting management tasks"""
        action = data.get("action")
        meeting_id = data.get("meeting_id")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                "users/{user_id}/onlineMeetings",
                data=data.get("settings", {})
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"users/{user_id}/onlineMeetings/{meeting_id}",
                data=data.get("settings", {})
            )
        elif action == "get":
            return await self.graph_client._make_request(
                "GET",
                f"users/{user_id}/onlineMeetings/{meeting_id}"
            )
        elif action == "delete":
            return await self.graph_client._make_request(
                "DELETE",
                f"users/{user_id}/onlineMeetings/{meeting_id}"
            )
        else:
            raise ValueError(f"Unknown meeting management action: {action}")
    
    async def _handle_policy_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Teams policy management tasks"""
        action = data.get("action")
        policy_type = data.get("policy_type")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                f"policies/teamsApps/{policy_type}Policies",
                data=data.get("settings", {})
            )
        elif action == "update":
            policy_id = data["policy_id"]
            return await self.graph_client._make_request(
                "PATCH",
                f"policies/teamsApps/{policy_type}Policies/{policy_id}",
                data=data.get("settings", {})
            )
        elif action == "delete":
            policy_id = data["policy_id"]
            return await self.graph_client._make_request(
                "DELETE",
                f"policies/teamsApps/{policy_type}Policies/{policy_id}"
            )
        elif action == "assign":
            return await self.graph_client._make_request(
                "POST",
                "policies/teamsApps/assignments",
                data=data.get("settings", {})
            )
        else:
            raise ValueError(f"Unknown policy management action: {action}")
    
    async def _handle_app_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Teams app management tasks"""
        action = data.get("action")
        app_id = data.get("app_id")
        
        if action == "install":
            return await self.graph_client._make_request(
                "POST",
                f"teams/{data['team_id']}/installedApps",
                data={
                    "teamsApp@odata.bind": f"https://graph.microsoft.com/v1.0/appCatalogs/teamsApps/{app_id}"
                }
            )
        elif action == "uninstall":
            return await self.graph_client._make_request(
                "DELETE",
                f"teams/{data['team_id']}/installedApps/{app_id}"
            )
        elif action == "list":
            return await self.graph_client._make_request(
                "GET",
                f"teams/{data['team_id']}/installedApps?$expand=teamsApp"
            )
        else:
            raise ValueError(f"Unknown app management action: {action}")
    
    async def cleanup(self):
        """Cleanup resources"""
        # No specific cleanup needed as we're using the graph client from m365_admin_agent
