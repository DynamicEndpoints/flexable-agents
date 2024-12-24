import asyncio
import logging
from typing import Dict, Any, List
import json
from pathlib import Path

from src.agents.m365_admin_agent import M365AdminAgent
from src.core.base import Task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def onboard_new_employee(
    admin_agent: M365AdminAgent,
    employee_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Workflow to onboard a new employee:
    1. Create user account
    2. Assign licenses
    3. Add to groups
    4. Create Teams workspace
    5. Generate welcome email
    """
    results = {}
    
    # 1. Create user account
    user_result = await admin_agent.process_task(Task(
        task_type="user_management",
        input_data={
            "action": "create_user",
            "display_name": employee_data["name"],
            "user_principal_name": employee_data["email"],
            "password": employee_data["initial_password"],
            "department": employee_data["department"]
        }
    ))
    results["user_creation"] = user_result.output
    user_id = user_result.output["id"]
    
    # 2. Assign licenses
    for license_id in employee_data["licenses"]:
        license_result = await admin_agent.process_task(Task(
            task_type="license_management",
            input_data={
                "action": "assign_license",
                "user_id": user_id,
                "license_id": license_id
            }
        ))
        results.setdefault("license_assignments", []).append(license_result.output)
    
    # 3. Add to groups
    for group_id in employee_data["groups"]:
        group_result = await admin_agent.process_task(Task(
            task_type="group_management",
            input_data={
                "action": "add_member",
                "group_id": group_id,
                "user_id": user_id
            }
        ))
        results.setdefault("group_assignments", []).append(group_result.output)
    
    # 4. Create Teams workspace
    team_result = await admin_agent.process_task(Task(
        task_type="teams_management",
        input_data={
            "action": "create_team",
            "display_name": f"{employee_data['department']} - {employee_data['name']}",
            "description": f"Workspace for {employee_data['name']}",
            "owners": [user_id]
        }
    ))
    results["teams_workspace"] = team_result.output
    
    return results

async def generate_security_report(
    admin_agent: M365AdminAgent,
    report_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive security report:
    1. Get security alerts
    2. Get device compliance
    3. Generate usage report
    4. Compile findings
    """
    results = {}
    
    # 1. Get security alerts
    alerts_result = await admin_agent.process_task(Task(
        task_type="security_management",
        input_data={
            "action": "get_security_alerts",
            "filter": "severity eq 'high'",
            "top": 100
        }
    ))
    results["security_alerts"] = alerts_result.output
    
    # 2. Get device compliance
    devices_result = await admin_agent.process_task(Task(
        task_type="device_management",
        input_data={
            "action": "get_devices",
            "filter": "complianceState eq 'noncompliant'"
        }
    ))
    results["noncompliant_devices"] = devices_result.output
    
    # 3. Generate usage report
    usage_result = await admin_agent.process_task(Task(
        task_type="report_generation",
        input_data={
            "report_type": "getOffice365ActiveUserDetail",
            "period": "D30",
            "format": "json"
        }
    ))
    results["usage_report"] = usage_result.output
    
    return results

async def main():
    # Load configuration
    with open("config/m365_config.json") as f:
        config = json.load(f)
    
    # Initialize agent
    admin_agent = M365AdminAgent(
        agent_id="m365_admin",
        work_dir="work_files/m365",
        tenant_id=config["tenant_id"],
        client_id=config["client_id"],
        client_secret=config["client_secret"]
    )
    
    try:
        # Example 1: Onboard new employee
        employee_data = {
            "name": "John Doe",
            "email": "john.doe@company.com",
            "initial_password": "Welcome2024!",
            "department": "Engineering",
            "licenses": [
                "c42b9cae-ea29-444e-9e6b-3301c2b6d36e",  # M365 E3
                "f30db892-07e9-47e9-837c-80727f46fd3d"   # Power BI Pro
            ],
            "groups": [
                "engineering-team",
                "all-employees"
            ]
        }
        
        onboarding_result = await onboard_new_employee(admin_agent, employee_data)
        logger.info("Employee onboarding completed: %s", json.dumps(onboarding_result, indent=2))
        
        # Example 2: Generate security report
        report_config = {
            "period": "D30",
            "include_alerts": True,
            "include_devices": True,
            "include_usage": True
        }
        
        security_report = await generate_security_report(admin_agent, report_config)
        logger.info("Security report generated: %s", json.dumps(security_report, indent=2))
    
    finally:
        # Cleanup
        await admin_agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
