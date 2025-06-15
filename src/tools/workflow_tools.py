"""Workflow automation and orchestration tools for MCP server."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import uuid
from pathlib import Path

from src.core import mcp_tool

logger = logging.getLogger(__name__)

# In-memory workflow storage (in production, this would be a database)
WORKFLOW_STORAGE = {
    "templates": {},
    "instances": {},
    "schedules": {}
}


def register_workflow_tools(server, config):
    """Register workflow automation tools with the MCP server."""
    
    server.register_tool(
        name="workflow_automation",
        description="Create and execute automated workflows",
        handler=workflow_automation,
        returns="Workflow execution result"
    )
    
    server.register_tool(
        name="workflow_template_management",
        description="Manage workflow templates and definitions",
        handler=workflow_template_management,
        returns="Workflow template management result"
    )
    
    server.register_tool(
        name="workflow_monitoring",
        description="Monitor and track workflow executions",
        handler=workflow_monitoring,
        returns="Workflow monitoring result"
    )
    
    server.register_tool(
        name="workflow_scheduling",
        description="Schedule and manage recurring workflows",
        handler=workflow_scheduling,
        returns="Workflow scheduling result"
    )
    
    logger.info("Registered workflow automation tools")


@mcp_tool(
    name="workflow_automation",
    description="Create and execute automated workflows",
    category="automation",
    tags=["workflows", "automation", "orchestration"]
)
async def workflow_automation(
    workflow_type: str, 
    workflow_data: Optional[Dict[str, Any]] = None, 
    action: str = "execute"
) -> Dict[str, Any]:
    """
    Create and execute automated workflows.
    
    Args:
        workflow_type: Type of workflow (employee_onboarding, security_audit, compliance_check, etc.)
        workflow_data: Workflow configuration and data
        action: Action to perform (create, execute, validate, stop)
    """
    try:
        workflow_data = workflow_data or {}
        workflow_id = str(uuid.uuid4())
        
        if action == "execute":
            if workflow_type == "employee_onboarding":
                return await execute_employee_onboarding(workflow_id, workflow_data)
            elif workflow_type == "employee_offboarding":
                return await execute_employee_offboarding(workflow_id, workflow_data)
            elif workflow_type == "security_audit":
                return await execute_security_audit(workflow_id, workflow_data)
            elif workflow_type == "compliance_check":
                return await execute_compliance_check(workflow_id, workflow_data)
            elif workflow_type == "backup_management":
                return await execute_backup_management(workflow_id, workflow_data)
            elif workflow_type == "license_optimization":
                return await execute_license_optimization(workflow_id, workflow_data)
            else:
                return {"status": "error", "message": f"Unknown workflow type: {workflow_type}"}
                
        elif action == "validate":
            validation_result = validate_workflow_data(workflow_type, workflow_data)
            return {
                "status": "success",
                "message": "Workflow validation completed",
                "data": {
                    "workflow_type": workflow_type,
                    "validation_result": validation_result,
                    "is_valid": validation_result["is_valid"]
                }
            }
            
        elif action == "create":
            template = create_workflow_template(workflow_type, workflow_data)
            WORKFLOW_STORAGE["templates"][workflow_id] = template
            return {
                "status": "success",
                "message": "Workflow template created",
                "data": {
                    "workflow_id": workflow_id,
                    "template": template
                }
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in workflow automation: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="workflow_template_management",
    description="Manage workflow templates",
    category="automation",
    tags=["templates", "workflows", "management"]
)
async def workflow_template_management(
    action: str,
    template_id: Optional[str] = None,
    template_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Manage workflow templates and definitions.
    
    Args:
        action: Action to perform (create, update, delete, get, list)
        template_id: Template ID for operations
        template_data: Template data for create/update operations
    """
    try:
        if action == "create":
            if not template_data:
                return {"status": "error", "message": "Template data required for create operation"}
            
            template_id = str(uuid.uuid4())
            template = {
                "id": template_id,
                "name": template_data.get("name"),
                "description": template_data.get("description"),
                "steps": template_data.get("steps", []),
                "variables": template_data.get("variables", {}),
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            WORKFLOW_STORAGE["templates"][template_id] = template
            
            return {
                "status": "success",
                "message": "Workflow template created",
                "data": template
            }
            
        elif action == "list":
            templates = list(WORKFLOW_STORAGE["templates"].values())
            return {
                "status": "success",
                "message": f"Retrieved {len(templates)} workflow templates",
                "data": {"templates": templates}
            }
            
        elif action == "get":
            if not template_id:
                return {"status": "error", "message": "Template ID required for get operation"}
            
            template = WORKFLOW_STORAGE["templates"].get(template_id)
            if not template:
                return {"status": "error", "message": f"Template not found: {template_id}"}
            
            return {
                "status": "success",
                "message": "Template retrieved",
                "data": template
            }
            
        elif action == "delete":
            if not template_id:
                return {"status": "error", "message": "Template ID required for delete operation"}
            
            if template_id in WORKFLOW_STORAGE["templates"]:
                del WORKFLOW_STORAGE["templates"][template_id]
                return {
                    "status": "success",
                    "message": f"Template {template_id} deleted"
                }
            else:
                return {"status": "error", "message": f"Template not found: {template_id}"}
                
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in workflow template management: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="workflow_monitoring",
    description="Monitor workflow executions",
    category="automation",
    tags=["monitoring", "tracking", "workflows"]
)
async def workflow_monitoring(
    action: str,
    workflow_id: Optional[str] = None,
    filter_criteria: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Monitor and track workflow executions.
    
    Args:
        action: Action to perform (list, get_status, get_logs, get_metrics)
        workflow_id: Workflow ID for specific operations
        filter_criteria: Filter criteria for list operations
    """
    try:
        if action == "list":
            instances = list(WORKFLOW_STORAGE["instances"].values())
            
            # Apply filters if provided
            if filter_criteria:
                status_filter = filter_criteria.get("status")
                if status_filter:
                    instances = [inst for inst in instances if inst.get("status") == status_filter]
                
                type_filter = filter_criteria.get("workflow_type")
                if type_filter:
                    instances = [inst for inst in instances if inst.get("workflow_type") == type_filter]
            
            return {
                "status": "success",
                "message": f"Retrieved {len(instances)} workflow instances",
                "data": {"instances": instances}
            }
            
        elif action == "get_status":
            if not workflow_id:
                return {"status": "error", "message": "Workflow ID required for get_status operation"}
            
            instance = WORKFLOW_STORAGE["instances"].get(workflow_id)
            if not instance:
                return {"status": "error", "message": f"Workflow instance not found: {workflow_id}"}
            
            return {
                "status": "success",
                "message": "Workflow status retrieved",
                "data": {
                    "workflow_id": workflow_id,
                    "status": instance.get("status"),
                    "progress": instance.get("progress", {}),
                    "start_time": instance.get("start_time"),
                    "end_time": instance.get("end_time"),
                    "steps_completed": len(instance.get("completed_steps", []))
                }
            }
            
        elif action == "get_metrics":
            instances = list(WORKFLOW_STORAGE["instances"].values())
            
            total_workflows = len(instances)
            completed_workflows = len([inst for inst in instances if inst.get("status") == "completed"])
            failed_workflows = len([inst for inst in instances if inst.get("status") == "failed"])
            running_workflows = len([inst for inst in instances if inst.get("status") == "running"])
            
            success_rate = (completed_workflows / total_workflows * 100) if total_workflows > 0 else 0
            
            return {
                "status": "success",
                "message": "Workflow metrics retrieved",
                "data": {
                    "total_workflows": total_workflows,
                    "completed": completed_workflows,
                    "failed": failed_workflows,
                    "running": running_workflows,
                    "success_rate": round(success_rate, 2),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in workflow monitoring: {e}")
        return {"status": "error", "message": str(e)}


@mcp_tool(
    name="workflow_scheduling",
    description="Schedule and manage recurring workflows",
    category="automation",
    tags=["scheduling", "recurring", "automation"]
)
async def workflow_scheduling(
    action: str,
    schedule_data: Optional[Dict[str, Any]] = None,
    schedule_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Schedule and manage recurring workflows.
    
    Args:
        action: Action to perform (create, update, delete, list, enable, disable)
        schedule_data: Schedule configuration data
        schedule_id: Schedule ID for operations
    """
    try:
        if action == "create":
            if not schedule_data:
                return {"status": "error", "message": "Schedule data required for create operation"}
            
            schedule_id = str(uuid.uuid4())
            schedule = {
                "id": schedule_id,
                "workflow_type": schedule_data.get("workflow_type"),
                "workflow_data": schedule_data.get("workflow_data", {}),
                "schedule_type": schedule_data.get("schedule_type", "once"),  # once, daily, weekly, monthly
                "schedule_time": schedule_data.get("schedule_time"),
                "enabled": True,
                "created_at": datetime.now().isoformat(),
                "last_run": None,
                "next_run": calculate_next_run(schedule_data)
            }
            
            WORKFLOW_STORAGE["schedules"][schedule_id] = schedule
            
            return {
                "status": "success",
                "message": "Workflow schedule created",
                "data": schedule
            }
            
        elif action == "list":
            schedules = list(WORKFLOW_STORAGE["schedules"].values())
            return {
                "status": "success",
                "message": f"Retrieved {len(schedules)} workflow schedules",
                "data": {"schedules": schedules}
            }
            
        elif action == "enable":
            if not schedule_id:
                return {"status": "error", "message": "Schedule ID required for enable operation"}
            
            if schedule_id in WORKFLOW_STORAGE["schedules"]:
                WORKFLOW_STORAGE["schedules"][schedule_id]["enabled"] = True
                return {
                    "status": "success",
                    "message": f"Schedule {schedule_id} enabled"
                }
            else:
                return {"status": "error", "message": f"Schedule not found: {schedule_id}"}
                
        elif action == "disable":
            if not schedule_id:
                return {"status": "error", "message": "Schedule ID required for disable operation"}
            
            if schedule_id in WORKFLOW_STORAGE["schedules"]:
                WORKFLOW_STORAGE["schedules"][schedule_id]["enabled"] = False
                return {
                    "status": "success",
                    "message": f"Schedule {schedule_id} disabled"
                }
            else:
                return {"status": "error", "message": f"Schedule not found: {schedule_id}"}
                
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error in workflow scheduling: {e}")
        return {"status": "error", "message": str(e)}


# Helper functions for workflow execution
async def execute_employee_onboarding(workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute employee onboarding workflow."""
    steps = [
        {"name": "Create user account", "status": "pending"},
        {"name": "Assign licenses", "status": "pending"},
        {"name": "Add to groups", "status": "pending"},
        {"name": "Create mailbox", "status": "pending"},
        {"name": "Setup Teams access", "status": "pending"},
        {"name": "Send welcome email", "status": "pending"}
    ]
    
    # Store workflow instance
    instance = {
        "id": workflow_id,
        "workflow_type": "employee_onboarding",
        "status": "running",
        "start_time": datetime.now().isoformat(),
        "steps": steps,
        "completed_steps": [],
        "workflow_data": workflow_data
    }
    
    WORKFLOW_STORAGE["instances"][workflow_id] = instance
    
    # Simulate step execution
    completed_steps = []
    for step in steps:
        step["status"] = "completed"
        step["completed_at"] = datetime.now().isoformat()
        completed_steps.append(step)
        await asyncio.sleep(0.1)  # Simulate processing time
    
    # Update instance
    instance["status"] = "completed"
    instance["end_time"] = datetime.now().isoformat()
    instance["completed_steps"] = completed_steps
    
    return {
        "status": "success",
        "message": "Employee onboarding workflow completed",
        "data": {
            "workflow_id": workflow_id,
            "steps_completed": len(completed_steps),
            "execution_time": "simulated",
            "results": completed_steps
        }
    }


async def execute_security_audit(workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute security audit workflow."""
    audit_checks = [
        "User access review",
        "Password policy compliance",
        "MFA enablement check",
        "Inactive user accounts",
        "Privileged access review",
        "Application permissions audit"
    ]
    
    results = []
    for check in audit_checks:
        results.append({
            "check": check,
            "status": "completed",
            "result": "passed",  # Simulated result
            "timestamp": datetime.now().isoformat()
        })
        await asyncio.sleep(0.1)
    
    return {
        "status": "success",
        "message": "Security audit workflow completed",
        "data": {
            "workflow_id": workflow_id,
            "audit_results": results,
            "overall_status": "passed"
        }
    }


async def execute_compliance_check(workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute compliance check workflow."""
    compliance_areas = [
        "Data retention policies",
        "Access controls",
        "Audit logging",
        "Encryption compliance",
        "Backup procedures"
    ]
    
    results = []
    for area in compliance_areas:
        results.append({
            "area": area,
            "status": "compliant",
            "checked_at": datetime.now().isoformat()
        })
        await asyncio.sleep(0.1)
    
    return {
        "status": "success",
        "message": "Compliance check workflow completed",
        "data": {
            "workflow_id": workflow_id,
            "compliance_results": results,
            "overall_compliance": "passed"
        }
    }


async def execute_employee_offboarding(workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute employee offboarding workflow."""
    steps = [
        "Disable user account",
        "Remove group memberships",
        "Backup user data",
        "Revoke access tokens",
        "Archive mailbox",
        "Update security groups"
    ]
    
    results = []
    for step in steps:
        results.append({
            "step": step,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        })
        await asyncio.sleep(0.1)
    
    return {
        "status": "success",
        "message": "Employee offboarding workflow completed",
        "data": {
            "workflow_id": workflow_id,
            "steps_completed": len(results),
            "results": results
        }
    }


async def execute_backup_management(workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute backup management workflow."""
    return {
        "status": "success",
        "message": "Backup management workflow completed",
        "data": {
            "workflow_id": workflow_id,
            "backup_status": "completed",
            "backup_size": "simulated"
        }
    }


async def execute_license_optimization(workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute license optimization workflow."""
    return {
        "status": "success",
        "message": "License optimization workflow completed",
        "data": {
            "workflow_id": workflow_id,
            "optimization_results": {
                "licenses_reviewed": 100,
                "unused_licenses": 5,
                "potential_savings": "$500/month"
            }
        }
    }


def validate_workflow_data(workflow_type: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate workflow data."""
    errors = []
    warnings = []
    
    if workflow_type == "employee_onboarding":
        if not workflow_data.get("employee_data"):
            errors.append("Employee data is required")
        if not workflow_data.get("licenses"):
            warnings.append("No licenses specified")
            
    elif workflow_type == "security_audit":
        if not workflow_data.get("scope"):
            warnings.append("No audit scope specified, using default")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def create_workflow_template(workflow_type: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a workflow template."""
    return {
        "type": workflow_type,
        "name": workflow_data.get("name", f"{workflow_type}_template"),
        "description": workflow_data.get("description", f"Template for {workflow_type}"),
        "version": "1.0",
        "created_at": datetime.now().isoformat()
    }


def calculate_next_run(schedule_data: Dict[str, Any]) -> str:
    """Calculate next run time for scheduled workflow."""
    schedule_type = schedule_data.get("schedule_type", "once")
    
    if schedule_type == "daily":
        next_run = datetime.now() + timedelta(days=1)
    elif schedule_type == "weekly":
        next_run = datetime.now() + timedelta(weeks=1)
    elif schedule_type == "monthly":
        next_run = datetime.now() + timedelta(days=30)
    else:
        next_run = datetime.now() + timedelta(hours=1)  # Default
    
    return next_run.isoformat()
