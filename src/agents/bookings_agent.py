import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import aiohttp
from datetime import datetime, timedelta

from ..core.base import Agent, Task, TaskResult

logger = logging.getLogger(__name__)

class BookingsAgent(Agent):
    """Agent for managing Microsoft Bookings configurations and appointments"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        graph_client: Any  # Microsoft Graph client from m365_admin_agent
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "business_management",
                "staff_management",
                "service_management",
                "appointment_management",
                "customer_management",
                "schedule_management"
            ]
        )
        
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.graph_client = graph_client
        
        self.tools = [
            # Business Management
            {
                "name": "manage_business",
                "description": "Manage Bookings business",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            },
            # Staff Management
            {
                "name": "manage_staff",
                "description": "Manage staff members",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string"},
                        "staff_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            },
            # Service Management
            {
                "name": "manage_service",
                "description": "Manage bookable services",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "business_id": {"type": "string"},
                        "service_id": {"type": "string"},
                        "action": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                }
            }
        ]
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process Bookings management tasks"""
        try:
            if task.task_type == "business_management":
                output = await self._handle_business_management(task.input_data)
            elif task.task_type == "staff_management":
                output = await self._handle_staff_management(task.input_data)
            elif task.task_type == "service_management":
                output = await self._handle_service_management(task.input_data)
            elif task.task_type == "appointment_management":
                output = await self._handle_appointment_management(task.input_data)
            elif task.task_type == "customer_management":
                output = await self._handle_customer_management(task.input_data)
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
    
    async def _handle_business_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle business management tasks"""
        action = data.get("action")
        business_id = data.get("business_id")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                "solutions/bookingBusinesses",
                data=data.get("settings", {})
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"solutions/bookingBusinesses/{business_id}",
                data=data.get("settings", {})
            )
        elif action == "delete":
            return await self.graph_client._make_request(
                "DELETE",
                f"solutions/bookingBusinesses/{business_id}"
            )
        elif action == "publish":
            return await self.graph_client._make_request(
                "POST",
                f"solutions/bookingBusinesses/{business_id}/publish"
            )
        elif action == "unpublish":
            return await self.graph_client._make_request(
                "POST",
                f"solutions/bookingBusinesses/{business_id}/unpublish"
            )
        else:
            raise ValueError(f"Unknown business management action: {action}")
    
    async def _handle_staff_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle staff management tasks"""
        action = data.get("action")
        business_id = data.get("business_id")
        staff_id = data.get("staff_id")
        
        if action == "add":
            return await self.graph_client._make_request(
                "POST",
                f"solutions/bookingBusinesses/{business_id}/staffMembers",
                data=data.get("settings", {})
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"solutions/bookingBusinesses/{business_id}/staffMembers/{staff_id}",
                data=data.get("settings", {})
            )
        elif action == "delete":
            return await self.graph_client._make_request(
                "DELETE",
                f"solutions/bookingBusinesses/{business_id}/staffMembers/{staff_id}"
            )
        elif action == "list":
            return await self.graph_client._make_request(
                "GET",
                f"solutions/bookingBusinesses/{business_id}/staffMembers"
            )
        else:
            raise ValueError(f"Unknown staff management action: {action}")
    
    async def _handle_service_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service management tasks"""
        action = data.get("action")
        business_id = data.get("business_id")
        service_id = data.get("service_id")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                f"solutions/bookingBusinesses/{business_id}/services",
                data=data.get("settings", {})
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"solutions/bookingBusinesses/{business_id}/services/{service_id}",
                data=data.get("settings", {})
            )
        elif action == "delete":
            return await self.graph_client._make_request(
                "DELETE",
                f"solutions/bookingBusinesses/{business_id}/services/{service_id}"
            )
        elif action == "list":
            return await self.graph_client._make_request(
                "GET",
                f"solutions/bookingBusinesses/{business_id}/services"
            )
        else:
            raise ValueError(f"Unknown service management action: {action}")
    
    async def _handle_appointment_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment management tasks"""
        action = data.get("action")
        business_id = data.get("business_id")
        appointment_id = data.get("appointment_id")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                f"solutions/bookingBusinesses/{business_id}/appointments",
                data=data.get("settings", {})
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"solutions/bookingBusinesses/{business_id}/appointments/{appointment_id}",
                data=data.get("settings", {})
            )
        elif action == "cancel":
            return await self.graph_client._make_request(
                "POST",
                f"solutions/bookingBusinesses/{business_id}/appointments/{appointment_id}/cancel",
                data=data.get("settings", {})
            )
        elif action == "list":
            return await self.graph_client._make_request(
                "GET",
                f"solutions/bookingBusinesses/{business_id}/appointments"
            )
        else:
            raise ValueError(f"Unknown appointment management action: {action}")
    
    async def _handle_customer_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer management tasks"""
        action = data.get("action")
        business_id = data.get("business_id")
        customer_id = data.get("customer_id")
        
        if action == "create":
            return await self.graph_client._make_request(
                "POST",
                f"solutions/bookingBusinesses/{business_id}/customers",
                data=data.get("settings", {})
            )
        elif action == "update":
            return await self.graph_client._make_request(
                "PATCH",
                f"solutions/bookingBusinesses/{business_id}/customers/{customer_id}",
                data=data.get("settings", {})
            )
        elif action == "delete":
            return await self.graph_client._make_request(
                "DELETE",
                f"solutions/bookingBusinesses/{business_id}/customers/{customer_id}"
            )
        elif action == "list":
            return await self.graph_client._make_request(
                "GET",
                f"solutions/bookingBusinesses/{business_id}/customers"
            )
        else:
            raise ValueError(f"Unknown customer management action: {action}")
    
    async def cleanup(self):
        """Cleanup resources"""
        # No specific cleanup needed as we're using the graph client from m365_admin_agent
