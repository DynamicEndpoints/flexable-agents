"""Azure tools for MCP server."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import asyncio
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.monitor import MonitorManagementClient
import aiohttp

from src.mcp import tool
from src.core import mcp_tool

logger = logging.getLogger(__name__)


class AzureResourceManager:
    """Azure Resource Manager for Azure operations."""
    
    def __init__(self, subscription_id: str, credential=None):
        self.subscription_id = subscription_id
        self.credential = credential or DefaultAzureCredential()
        
        # Initialize management clients
        self.resource_client = ResourceManagementClient(
            self.credential,
            subscription_id
        )
        self.compute_client = ComputeManagementClient(
            self.credential,
            subscription_id
        )
        self.network_client = NetworkManagementClient(
            self.credential,
            subscription_id
        )
        self.monitor_client = MonitorManagementClient(
            self.credential,
            subscription_id
        )


# Global Azure client instance
_azure_client: Optional[AzureResourceManager] = None


def initialize_azure_client(config):
    """Initialize the Azure Resource Manager client."""
    global _azure_client
    
    if config.azure.subscription_id:
        # Use client credentials if available
        if (config.m365.tenant_id and config.m365.client_id and config.m365.client_secret):
            credential = ClientSecretCredential(
                tenant_id=config.m365.tenant_id,
                client_id=config.m365.client_id,
                client_secret=config.m365.client_secret
            )
        else:
            credential = DefaultAzureCredential()
            
        _azure_client = AzureResourceManager(
            subscription_id=config.azure.subscription_id,
            credential=credential
        )


def register_azure_tools(server, config):
    """Register Azure tools with the MCP server."""
    
    # Initialize Azure client
    initialize_azure_client(config)
    
    server.register_tool(
        name="azure_resource_management",
        description="Manage Azure cloud resources and infrastructure", 
        handler=azure_resource_management,
        returns="Azure resource operation result"
    )
    
    server.register_tool(
        name="cost_analysis",
        description="Analyze and optimize cloud costs",
        handler=cost_analysis,
        returns="Cost analysis report"
    )
    
    server.register_tool(
        name="azure_vm_management",
        description="Manage Azure virtual machines",
        handler=azure_vm_management,
        returns="VM management operation result"
    )
    
    server.register_tool(
        name="azure_network_management",
        description="Manage Azure network resources",
        handler=azure_network_management,
        returns="Network management operation result"
    )
    
    logger.info("Registered Azure tools")


@mcp_tool(
    name="azure_resource_management",
    description="Manage Azure resources",
    category="azure",
    tags=["azure", "infrastructure", "resources"]
)
async def azure_resource_management(
    action: str, 
    resource_type: Optional[str] = None, 
    resource_group: Optional[str] = None,
    resource_name: Optional[str] = None,
    resource_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Manage Azure cloud resources.
    
    Args:
        action: Action to perform (create, update, delete, get, list)
        resource_type: Type of resource (resourceGroup, storageAccount, etc.)
        resource_group: Resource group name
        resource_name: Resource name
        resource_data: Resource configuration data
    """
    if not _azure_client:
        return {"status": "error", "message": "Azure client not initialized"}
    
    try:
        if action == "list_resource_groups":
            resource_groups = []
            for rg in _azure_client.resource_client.resource_groups.list():
                resource_groups.append({
                    "name": rg.name,
                    "location": rg.location,
                    "id": rg.id,
                    "tags": rg.tags
                })
            
            return {
                "status": "success",
                "data": {
                    "resource_groups": resource_groups,
                    "count": len(resource_groups)
                }
            }
            
        elif action == "create_resource_group":
            if not resource_name or not resource_data:
                return {"status": "error", "message": "Resource name and data required for create operation"}
            
            result = _azure_client.resource_client.resource_groups.create_or_update(
                resource_name,
                resource_data
            )
            
            return {
                "status": "success",
                "message": f"Resource group {resource_name} created successfully",
                "data": {
                    "name": result.name,
                    "location": result.location,
                    "id": result.id
                }
            }
            
        elif action == "delete_resource_group":
            if not resource_name:
                return {"status": "error", "message": "Resource name required for delete operation"}
            
            operation = _azure_client.resource_client.resource_groups.begin_delete(resource_name)
            
            return {
                "status": "success",
                "message": f"Resource group {resource_name} deletion initiated",
                "data": {"operation_id": operation.continuation_token()}
            }
            
        elif action == "list_resources":
            if not resource_group:
                return {"status": "error", "message": "Resource group required for list resources operation"}
            
            resources = []
            for resource in _azure_client.resource_client.resources.list_by_resource_group(resource_group):
                resources.append({
                    "name": resource.name,
                    "type": resource.type,
                    "location": resource.location,
                    "id": resource.id
                })
            
            return {
                "status": "success",
                "data": {
                    "resources": resources,
                    "count": len(resources),
                    "resource_group": resource_group
                }
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in Azure resource management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="azure_vm_management",
    description="Manage Azure virtual machines",
    category="azure",
    tags=["azure", "vm", "compute"]
)
async def azure_vm_management(
    action: str,
    resource_group: Optional[str] = None,
    vm_name: Optional[str] = None,
    vm_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Manage Azure virtual machines.
    
    Args:
        action: Action to perform (create, start, stop, restart, delete, get, list)
        resource_group: Resource group name
        vm_name: Virtual machine name
        vm_data: VM configuration data for create operations
    """
    if not _azure_client:
        return {"status": "error", "message": "Azure client not initialized"}
    
    try:
        if action == "list":
            if resource_group:
                vms = []
                for vm in _azure_client.compute_client.virtual_machines.list(resource_group):
                    vms.append({
                        "name": vm.name,
                        "id": vm.id,
                        "location": vm.location,
                        "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else None,
                        "provisioning_state": vm.provisioning_state
                    })
            else:
                vms = []
                for vm in _azure_client.compute_client.virtual_machines.list_all():
                    vms.append({
                        "name": vm.name,
                        "id": vm.id,
                        "location": vm.location,
                        "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else None,
                        "provisioning_state": vm.provisioning_state
                    })
            
            return {
                "status": "success",
                "data": {
                    "virtual_machines": vms,
                    "count": len(vms)
                }
            }
            
        elif action == "get":
            if not resource_group or not vm_name:
                return {"status": "error", "message": "Resource group and VM name required for get operation"}
            
            vm = _azure_client.compute_client.virtual_machines.get(resource_group, vm_name)
            
            return {
                "status": "success",
                "data": {
                    "name": vm.name,
                    "id": vm.id,
                    "location": vm.location,
                    "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else None,
                    "provisioning_state": vm.provisioning_state,
                    "os_type": vm.storage_profile.os_disk.os_type if vm.storage_profile and vm.storage_profile.os_disk else None
                }
            }
            
        elif action == "start":
            if not resource_group or not vm_name:
                return {"status": "error", "message": "Resource group and VM name required for start operation"}
            
            operation = _azure_client.compute_client.virtual_machines.begin_start(resource_group, vm_name)
            
            return {
                "status": "success",
                "message": f"VM {vm_name} start operation initiated",
                "data": {"operation_id": operation.continuation_token()}
            }
            
        elif action == "stop":
            if not resource_group or not vm_name:
                return {"status": "error", "message": "Resource group and VM name required for stop operation"}
            
            operation = _azure_client.compute_client.virtual_machines.begin_power_off(resource_group, vm_name)
            
            return {
                "status": "success",
                "message": f"VM {vm_name} stop operation initiated",
                "data": {"operation_id": operation.continuation_token()}
            }
            
        elif action == "restart":
            if not resource_group or not vm_name:
                return {"status": "error", "message": "Resource group and VM name required for restart operation"}
            
            operation = _azure_client.compute_client.virtual_machines.begin_restart(resource_group, vm_name)
            
            return {
                "status": "success",
                "message": f"VM {vm_name} restart operation initiated",
                "data": {"operation_id": operation.continuation_token()}
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in Azure VM management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="azure_network_management",
    description="Manage Azure network resources",
    category="azure",
    tags=["azure", "network", "infrastructure"]
)
async def azure_network_management(
    action: str,
    resource_group: Optional[str] = None,
    network_name: Optional[str] = None,
    network_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Manage Azure network resources.
    
    Args:
        action: Action to perform (create_vnet, list_vnets, get_vnet, delete_vnet)
        resource_group: Resource group name
        network_name: Network resource name
        network_data: Network configuration data
    """
    if not _azure_client:
        return {"status": "error", "message": "Azure client not initialized"}
    
    try:
        if action == "list_vnets":
            if resource_group:
                vnets = []
                for vnet in _azure_client.network_client.virtual_networks.list(resource_group):
                    vnets.append({
                        "name": vnet.name,
                        "id": vnet.id,
                        "location": vnet.location,
                        "address_space": vnet.address_space.address_prefixes if vnet.address_space else None,
                        "provisioning_state": vnet.provisioning_state
                    })
            else:
                vnets = []
                for vnet in _azure_client.network_client.virtual_networks.list_all():
                    vnets.append({
                        "name": vnet.name,
                        "id": vnet.id,
                        "location": vnet.location,
                        "address_space": vnet.address_space.address_prefixes if vnet.address_space else None,
                        "provisioning_state": vnet.provisioning_state
                    })
            
            return {
                "status": "success",
                "data": {
                    "virtual_networks": vnets,
                    "count": len(vnets)
                }
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in Azure network management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="cost_analysis",
    description="Analyze cloud costs",
    category="azure",
    tags=["azure", "cost", "optimization", "billing"]
)
async def cost_analysis(
    scope: str = "subscription", 
    time_period: str = "month", 
    resource_group: Optional[str] = None,
    detailed: bool = False
) -> Dict[str, Any]:
    """
    Analyze and optimize cloud costs.
    
    Args:
        scope: Analysis scope (subscription, resource_group, resource)
        time_period: Time period for analysis (day, week, month, year)
        resource_group: Specific resource group to analyze
        detailed: Whether to include detailed cost breakdown
    """
    if not _azure_client:
        return {"status": "error", "message": "Azure client not initialized"}
    
    try:
        # This is a simplified cost analysis
        # In a real implementation, you would use Azure Cost Management APIs
        
        analysis_result = {
            "scope": scope,
            "time_period": time_period,
            "resource_group": resource_group,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_cost": 0.0,
                "currency": "USD",
                "period_start": (datetime.now() - timedelta(days=30)).isoformat(),
                "period_end": datetime.now().isoformat()
            },
            "recommendations": [
                {
                    "type": "vm_rightsizing",
                    "description": "Consider downsizing underutilized VMs",
                    "potential_savings": "15-30%"
                },
                {
                    "type": "storage_optimization",
                    "description": "Move infrequently accessed data to cool storage",
                    "potential_savings": "40-60%"
                }
            ]
        }
        
        if detailed:
            # Get resource groups for detailed analysis
            resource_groups = []
            for rg in _azure_client.resource_client.resource_groups.list():
                resources = []
                for resource in _azure_client.resource_client.resources.list_by_resource_group(rg.name):
                    resources.append({
                        "name": resource.name,
                        "type": resource.type,
                        "location": resource.location
                    })
                
                resource_groups.append({
                    "name": rg.name,
                    "location": rg.location,
                    "resource_count": len(resources),
                    "estimated_monthly_cost": len(resources) * 10.0  # Simplified estimation
                })
            
            analysis_result["detailed_breakdown"] = {
                "resource_groups": resource_groups
            }
        
        return {
            "status": "success",
            "data": analysis_result
        }
        
    except Exception as e:
        logger.error(f"Error in cost analysis: {e}")
        return {"status": "error", "message": str(e)}
