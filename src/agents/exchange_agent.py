import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import aiohttp
from datetime import datetime, timedelta

from ..core.base import Agent, Task, TaskResult

logger = logging.getLogger(__name__)

class ExchangeAgent(Agent):
    """Agent for managing Microsoft Exchange Online configurations and policies"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        graph_client: Any  # Microsoft Graph client from m365_admin_agent
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "mailbox_management",
                "calendar_management",
                "distribution_group_management",
                "mail_flow_management",
                "compliance_management"
            ]
        )
        
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.graph_client = graph_client
        
        self.tools = [
            # Mailbox Management
            {
                "name": "manage_mailbox",
                "description": "Manage Exchange mailbox",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            },
            # Calendar Management
            {
                "name": "manage_calendar",
                "description": "Manage calendar settings",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            },
            # Distribution Group Management
            {
                "name": "manage_distribution_group",
                "description": "Manage distribution groups",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            }
        ]
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process Exchange management tasks"""
        try:
            if task.task_type == "mailbox_management":
                output = await self._handle_mailbox_management(task.input_data)
            elif task.task_type == "calendar_management":
                output = await self._handle_calendar_management(task.input_data)
            elif task.task_type == "distribution_group_management":
                output = await self._handle_distribution_group_management(task.input_data)
            elif task.task_type == "mail_flow_management":
                output = await self._handle_mail_flow_management(task.input_data)
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
    
    async def _handle_mailbox_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mailbox management tasks"""
        action = data.get("action")
        user_id = data.get("user_id")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                "users",
                data={
                    **data.get("settings", {}),
                    "accountEnabled": True,
                    "mailEnabled": True
                }
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"users/{user_id}",
                data=data.get("settings", {})
            )
        elif action == "get":
            return await self.graph_client._make_request(
                "GET",
                f"users/{user_id}/mailboxSettings"
            )
        elif action == "set_auto_reply":
            return await self.graph_client._make_request(
                "PATCH",
                f"users/{user_id}/mailboxSettings",
                data={
                    "automaticRepliesSetting": data.get("settings", {})
                }
            )
        elif action == "forward_email":
            return await self.graph_client._make_request(
                "PATCH",
                f"users/{user_id}/mailboxSettings",
                data={
                    "forwardingSettings": data.get("settings", {})
                }
            )
        else:
            raise ValueError(f"Unknown mailbox management action: {action}")
    
    async def _handle_calendar_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calendar management tasks"""
        action = data.get("action")
        user_id = data.get("user_id")
        
        if action == "create_event":
            return await self.graph_client._make_request(
                "POST",
                f"users/{user_id}/calendar/events",
                data=data.get("settings", {})
            )
        elif action == "update_event":
            event_id = data["event_id"]
            return await self.graph_client._make_request(
                "PATCH",
                f"users/{user_id}/calendar/events/{event_id}",
                data=data.get("settings", {})
            )
        elif action == "get_events":
            return await self.graph_client._make_request(
                "GET",
                f"users/{user_id}/calendar/events"
            )
        elif action == "delete_event":
            event_id = data["event_id"]
            return await self.graph_client._make_request(
                "DELETE",
                f"users/{user_id}/calendar/events/{event_id}"
            )
        else:
            raise ValueError(f"Unknown calendar management action: {action}")
    
    async def _handle_distribution_group_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle distribution group management tasks"""
        action = data.get("action")
        group_id = data.get("group_id")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                "groups",
                data={
                    **data.get("settings", {}),
                    "groupTypes": ["DynamicMembership"],
                    "mailEnabled": True,
                    "securityEnabled": False
                }
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"groups/{group_id}",
                data=data.get("settings", {})
            )
        elif action == "add_member":
            user_id = data["user_id"]
            return await self.graph_client._make_request(
                "POST",
                f"groups/{group_id}/members/$ref",
                data={
                    "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"
                }
            )
        elif action == "remove_member":
            user_id = data["user_id"]
            return await self.graph_client._make_request(
                "DELETE",
                f"groups/{group_id}/members/{user_id}/$ref"
            )
        else:
            raise ValueError(f"Unknown distribution group management action: {action}")
    
    async def _handle_mail_flow_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mail flow management tasks"""
        action = data.get("action")
        
        if action == "create_rule":
            return await self.graph_client._make_request(
                "POST",
                "admin/exchangeAdmin/mailFlowRules",
                data=data.get("settings", {})
            )
        elif action == "update_rule":
            rule_id = data["rule_id"]
            return await self.graph_client._make_request(
                "PATCH",
                f"admin/exchangeAdmin/mailFlowRules/{rule_id}",
                data=data.get("settings", {})
            )
        elif action == "delete_rule":
            rule_id = data["rule_id"]
            return await self.graph_client._make_request(
                "DELETE",
                f"admin/exchangeAdmin/mailFlowRules/{rule_id}"
            )
        elif action == "get_rules":
            return await self.graph_client._make_request(
                "GET",
                "admin/exchangeAdmin/mailFlowRules"
            )
        else:
            raise ValueError(f"Unknown mail flow management action: {action}")
    
    async def cleanup(self):
        """Cleanup resources"""
        # No specific cleanup needed as we're using the graph client from m365_admin_agent
