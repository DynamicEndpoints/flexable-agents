import asyncio
import logging
from typing import Dict, Any, List
import json
from pathlib import Path

from src.agents.m365_admin_agent import M365AdminAgent
from src.agents.sharepoint_dev_agent import SharePointDevAgent
from src.core.base import Task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntranetWorkflow:
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
        
        self.work_dir = Path("work_files/intranet")
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_intranet_solution(self, solution_name: str) -> Dict[str, Any]:
        """Create a modern intranet solution"""
        results = {}
        
        # 1. Create hub site
        logger.info("Creating hub site")
        hub_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "create_site",
                "site_name": f"{solution_name} Hub",
                "site_alias": f"{solution_name.lower()}-hub",
                "template": "CommunicationSite",
                "is_hub_site": True,
                "navigation": {
                    "global": [
                        {"title": "Home", "url": "/"},
                        {"title": "News", "url": "/news"},
                        {"title": "Departments", "url": "/departments"},
                        {"title": "Projects", "url": "/projects"}
                    ]
                }
            }
        ))
        results["hub_site"] = hub_result.output
        
        # 2. Create department sites
        logger.info("Creating department sites")
        departments = ["HR", "IT", "Finance", "Marketing"]
        department_results = []
        
        for dept in departments:
            dept_result = await self.sharepoint_dev_agent.process_task(Task(
                task_type="sharepoint_development",
                input_data={
                    "action": "create_site",
                    "site_name": f"{dept} Department",
                    "site_alias": f"{dept.lower()}-dept",
                    "template": "TeamSite",
                    "hub_site_id": hub_result.output["id"],
                    "features": {
                        "pages": True,
                        "news": True,
                        "document_center": True
                    }
                }
            ))
            department_results.append(dept_result.output)
        
        results["department_sites"] = department_results
        
        # 3. Create news site
        logger.info("Creating news site")
        news_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "create_site",
                "site_name": "Company News",
                "site_alias": "news",
                "template": "CommunicationSite",
                "hub_site_id": hub_result.output["id"],
                "features": {
                    "news_rotation": True,
                    "featured_news": True,
                    "news_digest": True
                }
            }
        ))
        results["news_site"] = news_result.output
        
        # 4. Create Power App for employee directory
        logger.info("Creating employee directory app")
        directory_app_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_apps_development",
            input_data={
                "action": "create_app",
                "app_name": "Employee Directory",
                "environment": self.config["power_platform"]["environments"]["dev"]["url"],
                "template": "blank",
                "data_sources": [
                    {
                        "type": "azure_ad",
                        "entity": "users"
                    }
                ],
                "screens": [
                    {
                        "name": "Directory",
                        "type": "gallery",
                        "layout": "people"
                    },
                    {
                        "name": "Profile",
                        "type": "form",
                        "layout": "two_column"
                    }
                ]
            }
        ))
        results["directory_app"] = directory_app_result.output
        
        # 5. Create Power Automate flows
        logger.info("Creating automation flows")
        flows_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_automate_development",
            input_data={
                "action": "create_flow",
                "flows": [
                    {
                        "name": "News Digest",
                        "trigger": {
                            "type": "schedule",
                            "frequency": "weekly"
                        },
                        "actions": [
                            {
                                "type": "get_news",
                                "site": news_result.output["url"]
                            },
                            {
                                "type": "send_email",
                                "template": "news_digest"
                            }
                        ]
                    },
                    {
                        "name": "Document Approval",
                        "trigger": {
                            "type": "sharepoint",
                            "event": "item_created"
                        },
                        "actions": [
                            {
                                "type": "start_approval",
                                "approvers": ["@{item.Department}"]
                            }
                        ]
                    }
                ]
            }
        ))
        results["automation_flows"] = flows_result.output
        
        # 6. Create Power BI dashboard
        logger.info("Creating intranet analytics")
        analytics_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_bi_development",
            input_data={
                "action": "create_report",
                "name": "Intranet Analytics",
                "data_sources": [
                    {
                        "type": "sharepoint",
                        "site": hub_result.output["url"],
                        "lists": ["Pages", "Documents"]
                    }
                ],
                "pages": [
                    {
                        "name": "Usage Overview",
                        "visuals": [
                            {
                                "type": "card",
                                "measure": "Total Visits"
                            },
                            {
                                "type": "line",
                                "measure": "Visits Over Time"
                            }
                        ]
                    },
                    {
                        "name": "Content Analysis",
                        "visuals": [
                            {
                                "type": "bar",
                                "measure": "Popular Pages"
                            },
                            {
                                "type": "pie",
                                "measure": "Content by Department"
                            }
                        ]
                    }
                ]
            }
        ))
        results["analytics"] = analytics_result.output
        
        return results
    
    async def deploy_spfx_components(self) -> Dict[str, Any]:
        """Deploy SPFx components for intranet customization"""
        results = {}
        
        # 1. Deploy header customization
        logger.info("Deploying custom header")
        header_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "deploy_solution",
                "solution_path": "solutions/custom-header",
                "components": [
                    {
                        "name": "CustomHeader",
                        "type": "ApplicationCustomizer",
                        "location": "ClientSideExtension.ApplicationCustomizer",
                        "properties": {
                            "testMessage": "Custom header loaded"
                        }
                    }
                ]
            }
        ))
        results["header"] = header_result.output
        
        # 2. Deploy news web part
        logger.info("Deploying news web part")
        news_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "deploy_solution",
                "solution_path": "solutions/news-webpart",
                "components": [
                    {
                        "name": "NewsRotator",
                        "type": "WebPart",
                        "properties": {
                            "newsSource": "site",
                            "numberOfItems": 5
                        }
                    }
                ]
            }
        ))
        results["news_webpart"] = news_result.output
        
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
    workflow = IntranetWorkflow(
        m365_agent=m365_agent,
        sharepoint_dev_agent=sharepoint_dev_agent,
        config_path="config/templates/sharepoint_dev_config_template.json"
    )
    
    try:
        # Create intranet solution
        intranet_result = await workflow.create_intranet_solution("Contoso")
        logger.info("Intranet solution created: %s", json.dumps(intranet_result, indent=2))
        
        # Deploy SPFx components
        spfx_result = await workflow.deploy_spfx_components()
        logger.info("SPFx components deployed: %s", json.dumps(spfx_result, indent=2))
    
    finally:
        # Cleanup
        await m365_agent.cleanup()
        await sharepoint_dev_agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
