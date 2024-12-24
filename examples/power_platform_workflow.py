import asyncio
import logging
from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.agents.m365_admin_agent import M365AdminAgent
from src.agents.sharepoint_dev_agent import SharePointDevAgent
from src.core.base import Task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PowerPlatformWorkflow:
    def __init__(
        self,
        m365_agent: M365AdminAgent,
        sharepoint_dev_agent: SharePointDevAgent,
        config_path: str
    ):
        self.m365_agent = m365_agent
        self.sharepoint_dev_agent = sharepoint_dev_agent
        
        # Load configuration
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.work_dir = Path("work_files/power_platform")
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_business_solution(self, solution_name: str) -> Dict[str, Any]:
        """Create a complete business solution with Power Apps, Power Automate, and SharePoint"""
        results = {}
        
        # 1. Create SharePoint lists for data storage
        logger.info("Creating SharePoint lists")
        lists_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "create_list",
                "site_url": self.config["sharepoint"]["development"]["environments"]["dev"]["site_url"],
                "lists": [
                    {
                        "title": f"{solution_name}_Projects",
                        "template": "Custom List",
                        "fields": [
                            {"name": "ProjectCode", "type": "Text"},
                            {"name": "Status", "type": "Choice", "choices": ["New", "Active", "Completed"]},
                            {"name": "StartDate", "type": "DateTime"},
                            {"name": "EndDate", "type": "DateTime"},
                            {"name": "Budget", "type": "Number"},
                            {"name": "Manager", "type": "User"}
                        ]
                    },
                    {
                        "title": f"{solution_name}_Tasks",
                        "template": "Custom List",
                        "fields": [
                            {"name": "ProjectId", "type": "Lookup", "list": f"{solution_name}_Projects"},
                            {"name": "TaskName", "type": "Text"},
                            {"name": "Status", "type": "Choice", "choices": ["Not Started", "In Progress", "Completed"]},
                            {"name": "AssignedTo", "type": "User"},
                            {"name": "DueDate", "type": "DateTime"}
                        ]
                    }
                ]
            }
        ))
        results["sharepoint_lists"] = lists_result.output
        
        # 2. Create Power App
        logger.info("Creating Power App")
        app_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_apps_development",
            input_data={
                "action": "create_app",
                "app_name": f"{solution_name}_App",
                "environment": self.config["power_platform"]["environments"]["dev"]["url"],
                "template": "blank",
                "data_sources": [
                    {
                        "type": "sharepoint",
                        "list_name": f"{solution_name}_Projects",
                        "site_url": self.config["sharepoint"]["development"]["environments"]["dev"]["site_url"]
                    },
                    {
                        "type": "sharepoint",
                        "list_name": f"{solution_name}_Tasks",
                        "site_url": self.config["sharepoint"]["development"]["environments"]["dev"]["site_url"]
                    }
                ],
                "screens": [
                    {
                        "name": "Projects",
                        "type": "gallery",
                        "data_source": f"{solution_name}_Projects"
                    },
                    {
                        "name": "Tasks",
                        "type": "gallery",
                        "data_source": f"{solution_name}_Tasks"
                    },
                    {
                        "name": "ProjectDetails",
                        "type": "form",
                        "data_source": f"{solution_name}_Projects"
                    }
                ]
            }
        ))
        results["power_app"] = app_result.output
        
        # 3. Create Power Automate flows
        logger.info("Creating Power Automate flows")
        flows_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_automate_development",
            input_data={
                "action": "create_flow",
                "flows": [
                    {
                        "name": f"{solution_name}_ProjectApproval",
                        "trigger": {
                            "type": "sharepoint",
                            "list": f"{solution_name}_Projects",
                            "event": "created"
                        },
                        "actions": [
                            {
                                "type": "approval",
                                "settings": {
                                    "approvers": ["@{triggerBody()?['Manager']}"],
                                    "subject": "New Project Approval Required",
                                    "message": "Please review and approve the new project"
                                }
                            },
                            {
                                "type": "condition",
                                "settings": {
                                    "if": "@equals(outputs('Approval')?['outcome'], 'Approve')",
                                    "then": [
                                        {
                                            "type": "update_sharepoint_item",
                                            "settings": {
                                                "list": f"{solution_name}_Projects",
                                                "id": "@triggerBody()?['ID']",
                                                "fields": {
                                                    "Status": "Active"
                                                }
                                            }
                                        }
                                    ],
                                    "else": [
                                        {
                                            "type": "update_sharepoint_item",
                                            "settings": {
                                                "list": f"{solution_name}_Projects",
                                                "id": "@triggerBody()?['ID']",
                                                "fields": {
                                                    "Status": "Rejected"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                    {
                        "name": f"{solution_name}_TaskNotification",
                        "trigger": {
                            "type": "sharepoint",
                            "list": f"{solution_name}_Tasks",
                            "event": "created"
                        },
                        "actions": [
                            {
                                "type": "send_email",
                                "settings": {
                                    "to": "@{triggerBody()?['AssignedTo']}",
                                    "subject": "New Task Assigned",
                                    "body": "You have been assigned a new task: @{triggerBody()?['TaskName']}"
                                }
                            },
                            {
                                "type": "teams_notification",
                                "settings": {
                                    "channel": "Project Updates",
                                    "message": "New task created: @{triggerBody()?['TaskName']}"
                                }
                            }
                        ]
                    }
                ]
            }
        ))
        results["power_automate_flows"] = flows_result.output
        
        # 4. Create Power BI report
        logger.info("Creating Power BI report")
        report_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_bi_development",
            input_data={
                "action": "create_report",
                "name": f"{solution_name}_Analytics",
                "data_sources": [
                    {
                        "type": "sharepoint",
                        "list": f"{solution_name}_Projects",
                        "fields": ["ProjectCode", "Status", "StartDate", "EndDate", "Budget"]
                    },
                    {
                        "type": "sharepoint",
                        "list": f"{solution_name}_Tasks",
                        "fields": ["ProjectId", "TaskName", "Status", "DueDate"]
                    }
                ],
                "pages": [
                    {
                        "name": "Project Overview",
                        "visuals": [
                            {
                                "type": "card",
                                "measure": "Total Projects"
                            },
                            {
                                "type": "pie",
                                "measure": "Projects by Status"
                            },
                            {
                                "type": "column",
                                "measure": "Budget by Project"
                            }
                        ]
                    },
                    {
                        "name": "Task Analysis",
                        "visuals": [
                            {
                                "type": "table",
                                "fields": ["TaskName", "Status", "DueDate"]
                            },
                            {
                                "type": "gauge",
                                "measure": "Task Completion Rate"
                            }
                        ]
                    }
                ]
            }
        ))
        results["power_bi_report"] = report_result.output
        
        return results
    
    async def deploy_solution(self, solution_name: str, environment: str) -> Dict[str, Any]:
        """Deploy the solution to specified environment"""
        results = {}
        
        # 1. Export solution
        logger.info(f"Exporting solution from {environment}")
        export_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_apps_development",
            input_data={
                "action": "export_solution",
                "solution_name": solution_name,
                "environment": self.config["power_platform"]["environments"][environment]["url"]
            }
        ))
        results["export"] = export_result.output
        
        # 2. Import to target environment
        logger.info(f"Importing solution to {environment}")
        import_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_apps_development",
            input_data={
                "action": "import_solution",
                "solution_path": export_result.output["solution_path"],
                "environment": self.config["power_platform"]["environments"][environment]["url"],
                "settings": {
                    "override_customizations": True,
                    "import_users": True
                }
            }
        ))
        results["import"] = import_result.output
        
        return results

async def main():
    # Load configuration
    with open("config/m365_config.json") as f:
        m365_config = json.load(f)
    
    with open("config/templates/sharepoint_dev_config_template.json") as f:
        sharepoint_config = json.load(f)
    
    # Initialize agents
    m365_agent = M365AdminAgent(
        agent_id="m365_admin",
        work_dir="work_files/m365",
        tenant_id=m365_config["tenant_id"],
        client_id=m365_config["client_id"],
        client_secret=m365_config["client_secret"]
    )
    
    sharepoint_dev_agent = SharePointDevAgent(
        agent_id="sharepoint_dev",
        work_dir="work_files/sharepoint_dev",
        graph_client=m365_agent,
        config=sharepoint_config
    )
    
    # Initialize workflow
    workflow = PowerPlatformWorkflow(
        m365_agent=m365_agent,
        sharepoint_dev_agent=sharepoint_dev_agent,
        config_path="config/templates/sharepoint_dev_config_template.json"
    )
    
    try:
        # Create business solution
        solution_result = await workflow.create_business_solution("ProjectManagement")
        logger.info("Business solution created: %s", json.dumps(solution_result, indent=2))
        
        # Deploy to production
        deployment_result = await workflow.deploy_solution("ProjectManagement", "prod")
        logger.info("Solution deployed: %s", json.dumps(deployment_result, indent=2))
    
    finally:
        # Cleanup
        await m365_agent.cleanup()
        await sharepoint_dev_agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
