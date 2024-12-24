import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import aiohttp
from datetime import datetime, timedelta

from ..core.base import Agent, Task, TaskResult

logger = logging.getLogger(__name__)

class IntuneAgent(Agent):
    """Agent for managing Microsoft Intune configurations and policies"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        graph_client: Any  # Microsoft Graph client from m365_admin_agent
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "device_management",
                "policy_management",
                "app_management",
                "compliance_management",
                "configuration_management"
            ]
        )
        
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.graph_client = graph_client
        
        self.tools = [
            # Device Management
            {
                "name": "manage_device",
                "description": "Manage Intune device",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            },
            # Policy Management
            {
                "name": "manage_policy",
                "description": "Manage Intune policies",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "policy_type": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            },
            # App Management
            {
                "name": "manage_app",
                "description": "Manage mobile apps",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "app_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            }
        ]
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process Intune management tasks"""
        try:
            if task.task_type == "device_management":
                output = await self._handle_device_management(task.input_data)
            elif task.task_type == "policy_management":
                output = await self._handle_policy_management(task.input_data)
            elif task.task_type == "app_management":
                output = await self._handle_app_management(task.input_data)
            elif task.task_type == "compliance_management":
                output = await self._handle_compliance_management(task.input_data)
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
    
    async def _handle_device_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle device management tasks"""
        action = data.get("action")
        device_id = data.get("device_id")
        
        if action == "wipe":
            return await self.graph_client._make_request(
                "POST",
                f"deviceManagement/managedDevices/{device_id}/wipe",
                data=data.get("settings", {})
            )
        elif action == "retire":
            return await self.graph_client._make_request(
                "POST",
                f"deviceManagement/managedDevices/{device_id}/retire",
                data=data.get("settings", {})
            )
        elif action == "sync":
            return await self.graph_client._make_request(
                "POST",
                f"deviceManagement/managedDevices/{device_id}/syncDevice",
                data=data.get("settings", {})
            )
        elif action == "get_info":
            return await self.graph_client._make_request(
                "GET",
                f"deviceManagement/managedDevices/{device_id}"
            )
        else:
            raise ValueError(f"Unknown device management action: {action}")
    
    async def _handle_policy_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle policy management tasks"""
        action = data.get("action")
        policy_type = data.get("policy_type")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                f"deviceManagement/{policy_type}Policies",
                data=data.get("settings", {})
            )
        elif action == "update":
            policy_id = data["policy_id"]
            return await self.graph_client._make_request(
                "PATCH",
                f"deviceManagement/{policy_type}Policies/{policy_id}",
                data=data.get("settings", {})
            )
        elif action == "delete":
            policy_id = data["policy_id"]
            return await self.graph_client._make_request(
                "DELETE",
                f"deviceManagement/{policy_type}Policies/{policy_id}"
            )
        elif action == "get":
            policy_id = data["policy_id"]
            return await self.graph_client._make_request(
                "GET",
                f"deviceManagement/{policy_type}Policies/{policy_id}"
            )
        elif action == "list":
            return await self.graph_client._make_request(
                "GET",
                f"deviceManagement/{policy_type}Policies"
            )
        else:
            raise ValueError(f"Unknown policy management action: {action}")
    
    async def _handle_app_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mobile app management tasks"""
        action = data.get("action")
        
        if action == "assign":
            app_id = data["app_id"]
            return await self.graph_client._make_request(
                "POST",
                f"deviceAppManagement/mobileApps/{app_id}/assign",
                data=data.get("settings", {})
            )
        elif action == "create":
            return await self.graph_client._make_request(
                "POST",
                "deviceAppManagement/mobileApps",
                data=data.get("settings", {})
            )
        elif action == "update":
            app_id = data["app_id"]
            return await self.graph_client._make_request(
                "PATCH",
                f"deviceAppManagement/mobileApps/{app_id}",
                data=data.get("settings", {})
            )
        elif action == "delete":
            app_id = data["app_id"]
            return await self.graph_client._make_request(
                "DELETE",
                f"deviceAppManagement/mobileApps/{app_id}"
            )
        elif action == "get":
            app_id = data["app_id"]
            return await self.graph_client._make_request(
                "GET",
                f"deviceAppManagement/mobileApps/{app_id}"
            )
        else:
            raise ValueError(f"Unknown app management action: {action}")
    
    async def _handle_compliance_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle compliance management tasks"""
        action = data.get("action")
        
        if action == "create_policy":
            return await self.graph_client._make_request(
                "POST",
                "deviceManagement/deviceCompliancePolicies",
                data=data.get("settings", {})
            )
        elif action == "update_policy":
            policy_id = data["policy_id"]
            return await self.graph_client._make_request(
                "PATCH",
                f"deviceManagement/deviceCompliancePolicies/{policy_id}",
                data=data.get("settings", {})
            )
        elif action == "get_device_compliance":
            device_id = data["device_id"]
            return await self.graph_client._make_request(
                "GET",
                f"deviceManagement/managedDevices/{device_id}/deviceCompliancePolicyStates"
            )
        elif action == "get_noncompliant_devices":
            return await self.graph_client._make_request(
                "GET",
                "deviceManagement/managedDevices",
                params={"$filter": "complianceState eq 'noncompliant'"}
            )
        else:
            raise ValueError(f"Unknown compliance management action: {action}")
    
    async def cleanup(self):
        """Cleanup resources"""
        # No specific cleanup needed as we're using the graph client from m365_admin_agent
