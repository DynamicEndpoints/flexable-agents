import asyncio
import logging
from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.agents.m365_admin_agent import M365AdminAgent
from src.agents.intune_agent import IntuneAgent
from src.agents.exchange_agent import ExchangeAgent
from src.agents.teams_agent import TeamsAgent
from src.core.base import Task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def employee_offboarding(
    m365_agent: M365AdminAgent,
    intune_agent: IntuneAgent,
    exchange_agent: ExchangeAgent,
    teams_agent: TeamsAgent,
    employee_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Comprehensive employee offboarding workflow:
    1. Disable user account
    2. Remove licenses
    3. Set up email forwarding
    4. Remove from groups and teams
    5. Wipe company devices
    6. Archive data
    7. Generate offboarding report
    """
    results = {}
    user_id = employee_data["user_id"]
    
    try:
        # 1. Disable user account and set out of office
        logger.info(f"Disabling account for user {user_id}")
        account_result = await m365_agent.process_task(Task(
            task_type="user_management",
            input_data={
                "action": "update_user",
                "user_id": user_id,
                "properties": {
                    "accountEnabled": False
                }
            }
        ))
        results["account_disabled"] = account_result.output
        
        # Set up out of office reply
        logger.info("Setting up out of office message")
        auto_reply_result = await exchange_agent.process_task(Task(
            task_type="mailbox_management",
            input_data={
                "action": "set_auto_reply",
                "user_id": user_id,
                "settings": {
                    "status": "Scheduled",
                    "scheduledStartDateTime": {
                        "dateTime": datetime.now().isoformat(),
                        "timeZone": "UTC"
                    },
                    "scheduledEndDateTime": {
                        "dateTime": (datetime.now() + timedelta(days=365)).isoformat(),
                        "timeZone": "UTC"
                    },
                    "externalReplyMessage": f"This employee is no longer with the company. Please contact {employee_data['manager_email']} for assistance.",
                    "internalReplyMessage": f"This employee is no longer with the company. Please contact {employee_data['manager_email']} for assistance."
                }
            }
        ))
        results["auto_reply_set"] = auto_reply_result.output
        
        # 2. Remove licenses
        logger.info("Removing licenses")
        for license_id in employee_data["licenses"]:
            license_result = await m365_agent.process_task(Task(
                task_type="license_management",
                input_data={
                    "action": "remove_license",
                    "user_id": user_id,
                    "license_id": license_id
                }
            ))
            results.setdefault("licenses_removed", []).append(license_result.output)
        
        # 3. Set up email forwarding
        logger.info("Setting up email forwarding")
        forward_result = await exchange_agent.process_task(Task(
            task_type="mailbox_management",
            input_data={
                "action": "forward_email",
                "user_id": user_id,
                "settings": {
                    "forwardingAddress": employee_data["manager_email"],
                    "forwardingSmtpAddress": employee_data["manager_email"],
                    "deliverToMailboxAndForward": True
                }
            }
        ))
        results["email_forwarding"] = forward_result.output
        
        # 4. Remove from groups and teams
        logger.info("Removing from groups and teams")
        # Get user's groups
        groups_result = await m365_agent.process_task(Task(
            task_type="user_management",
            input_data={
                "action": "get_memberships",
                "user_id": user_id
            }
        ))
        
        for group in groups_result.output.get("value", []):
            # Remove from group
            group_result = await m365_agent.process_task(Task(
                task_type="group_management",
                input_data={
                    "action": "remove_member",
                    "group_id": group["id"],
                    "user_id": user_id
                }
            ))
            results.setdefault("groups_removed", []).append(group_result.output)
            
            # If it's a team, handle Teams-specific cleanup
            if "team" in group:
                team_result = await teams_agent.process_task(Task(
                    task_type="team_management",
                    input_data={
                        "action": "remove_member",
                        "team_id": group["id"],
                        "user_id": user_id
                    }
                ))
                results.setdefault("teams_removed", []).append(team_result.output)
        
        # 5. Handle devices
        logger.info("Managing devices")
        # Get user's devices
        devices_result = await intune_agent.process_task(Task(
            task_type="device_management",
            input_data={
                "action": "get_devices",
                "filter": f"userPrincipalName eq '{employee_data['email']}'"
            }
        ))
        
        for device in devices_result.output.get("value", []):
            # Wipe device
            wipe_result = await intune_agent.process_task(Task(
                task_type="device_management",
                input_data={
                    "action": "wipe",
                    "device_id": device["id"]
                }
            ))
            results.setdefault("devices_wiped", []).append(wipe_result.output)
        
        # 6. Archive Teams chats and channels
        logger.info("Archiving Teams data")
        # Get user's teams
        teams_result = await teams_agent.process_task(Task(
            task_type="team_management",
            input_data={
                "action": "list_owned_teams",
                "user_id": user_id
            }
        ))
        
        for team in teams_result.output.get("value", []):
            # Archive team
            archive_result = await teams_agent.process_task(Task(
                task_type="team_management",
                input_data={
                    "action": "archive",
                    "team_id": team["id"],
                    "settings": {
                        "shouldSetSpoSiteReadOnlyForMembers": True
                    }
                }
            ))
            results.setdefault("teams_archived", []).append(archive_result.output)
        
        # 7. Generate offboarding report
        logger.info("Generating offboarding report")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(f"reports/offboarding_{user_id}_{timestamp}.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump({
                "user_id": user_id,
                "email": employee_data["email"],
                "offboarding_date": datetime.now().isoformat(),
                "actions_performed": results
            }, f, indent=2)
        
        results["report_path"] = str(report_path)
        logger.info(f"Offboarding completed successfully for user {user_id}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error during offboarding for user {user_id}: {str(e)}")
        raise

async def main():
    # Load configuration
    with open("config/m365_config.json") as f:
        config = json.load(f)
    
    # Initialize agents
    m365_agent = M365AdminAgent(
        agent_id="m365_admin",
        work_dir="work_files/m365",
        tenant_id=config["tenant_id"],
        client_id=config["client_id"],
        client_secret=config["client_secret"]
    )
    
    intune_agent = IntuneAgent(
        agent_id="intune_admin",
        work_dir="work_files/intune",
        graph_client=m365_agent
    )
    
    exchange_agent = ExchangeAgent(
        agent_id="exchange_admin",
        work_dir="work_files/exchange",
        graph_client=m365_agent
    )
    
    teams_agent = TeamsAgent(
        agent_id="teams_admin",
        work_dir="work_files/teams",
        graph_client=m365_agent
    )
    
    try:
        # Example offboarding
        employee_data = {
            "user_id": "john.doe@company.com",
            "email": "john.doe@company.com",
            "manager_email": "manager@company.com",
            "licenses": [
                "c42b9cae-ea29-444e-9e6b-3301c2b6d36e",  # M365 E3
                "f30db892-07e9-47e9-837c-80727f46fd3d"   # Power BI Pro
            ]
        }
        
        result = await employee_offboarding(
            m365_agent=m365_agent,
            intune_agent=intune_agent,
            exchange_agent=exchange_agent,
            teams_agent=teams_agent,
            employee_data=employee_data
        )
        
        logger.info("Offboarding completed: %s", json.dumps(result, indent=2))
    
    finally:
        # Cleanup
        await m365_agent.cleanup()
        await intune_agent.cleanup()
        await exchange_agent.cleanup()
        await teams_agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
