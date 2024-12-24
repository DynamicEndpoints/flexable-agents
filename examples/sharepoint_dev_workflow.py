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

class SharePointDevWorkflow:
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
        
        self.work_dir = Path("work_files/sharepoint_dev")
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    async def setup_development_environment(self) -> Dict[str, Any]:
        """Set up SharePoint development environment"""
        results = {}
        
        # 1. Create development site
        logger.info("Creating development site")
        site_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "create_site",
                "site_name": "Development Site",
                "site_alias": "dev-site",
                "template": "TeamSite",
                "is_public": False
            }
        ))
        results["development_site"] = site_result.output
        
        # 2. Set up content types
        logger.info("Setting up content types")
        content_types_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="information_architecture",
            input_data={
                "action": "create_content_type",
                "site_id": site_result.output["id"],
                "name": "Project Document",
                "description": "Content type for project documents",
                "fields": [
                    {
                        "name": "ProjectCode",
                        "type": "Text",
                        "required": True
                    },
                    {
                        "name": "DocumentStatus",
                        "type": "Choice",
                        "choices": ["Draft", "Review", "Final"]
                    }
                ]
            }
        ))
        results["content_types"] = content_types_result.output
        
        return results
    
    async def create_power_app_solution(self, solution_name: str) -> Dict[str, Any]:
        """Create a Power App solution"""
        results = {}
        
        # 1. Create Power App
        logger.info(f"Creating Power App: {solution_name}")
        app_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_apps_development",
            input_data={
                "action": "create_app",
                "app_name": solution_name,
                "environment": self.config["power_platform"]["environments"]["dev"]["url"],
                "template": "blank"
            }
        ))
        results["power_app"] = app_result.output
        
        # 2. Create associated flow
        logger.info("Creating associated Power Automate flow")
        flow_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_automate_development",
            input_data={
                "action": "create_flow",
                "flow_name": f"{solution_name}_Flow",
                "environment": self.config["power_platform"]["environments"]["dev"]["url"],
                "flow_definition": {
                    "triggers": {
                        "manual": {
                            "type": "manual",
                            "inputs": {}
                        }
                    },
                    "actions": {
                        "create_item": {
                            "type": "create_sharepoint_item",
                            "inputs": {
                                "site": "$(parameters.site_url)",
                                "list": "$(parameters.list_name)"
                            }
                        }
                    }
                }
            }
        ))
        results["power_automate_flow"] = flow_result.output
        
        return results
    
    async def migrate_sharepoint_site(self, source_url: str, target_url: str) -> Dict[str, Any]:
        """Migrate SharePoint site from source to target"""
        results = {}
        
        # 1. Assess migration environment
        logger.info("Assessing migration environment")
        assessment_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="migration_management",
            input_data={
                "action": "assess_environment",
                "source": {
                    "url": source_url,
                    "type": "on_premises"
                },
                "target": {
                    "url": target_url,
                    "type": "sharepoint_online"
                }
            }
        ))
        results["assessment"] = assessment_result.output
        
        # 2. Prepare for migration
        logger.info("Preparing for migration")
        prep_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="migration_management",
            input_data={
                "action": "prepare_migration",
                "source_url": source_url,
                "target_url": target_url,
                "settings": {
                    "create_target_locations": True,
                    "map_permissions": True
                }
            }
        ))
        results["preparation"] = prep_result.output
        
        # 3. Execute migration
        logger.info("Executing migration")
        migration_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="migration_management",
            input_data={
                "action": "execute_migration",
                "migration_tool": "ShareGate",
                "source_url": source_url,
                "target_url": target_url,
                "settings": self.config["migration"]["tools"]["sharegate"]["settings"]
            }
        ))
        results["migration"] = migration_result.output
        
        # 4. Validate migration
        logger.info("Validating migration")
        validation_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="migration_management",
            input_data={
                "action": "validate_migration",
                "source_url": source_url,
                "target_url": target_url,
                "validation_type": "full"
            }
        ))
        results["validation"] = validation_result.output
        
        return results
    
    async def deploy_spfx_solution(self, solution_path: str) -> Dict[str, Any]:
        """Deploy SPFx solution to SharePoint"""
        results = {}
        
        # 1. Deploy solution
        logger.info("Deploying SPFx solution")
        deployment_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "deploy_solution",
                "solution_path": solution_path,
                "target_site": self.config["sharepoint"]["development"]["environments"]["prod"]["site_url"],
                "settings": {
                    "skip_feature_deployment": False,
                    "override_data": True
                }
            }
        ))
        results["deployment"] = deployment_result.output
        
        # 2. Add web part to page
        logger.info("Adding web part to page")
        webpart_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "add_web_part",
                "target_site": self.config["sharepoint"]["development"]["environments"]["prod"]["site_url"],
                "page_name": "Home.aspx",
                "web_part": {
                    "name": "HelloWorld",
                    "properties": {
                        "description": "Hello from SPFx!"
                    }
                }
            }
        ))
        results["web_part"] = webpart_result.output
        
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
    workflow = SharePointDevWorkflow(
        m365_agent=m365_agent,
        sharepoint_dev_agent=sharepoint_dev_agent,
        config_path="config/templates/sharepoint_dev_config_template.json"
    )
    
    try:
        # Example: Set up development environment
        dev_result = await workflow.setup_development_environment()
        logger.info("Development environment setup: %s", json.dumps(dev_result, indent=2))
        
        # Example: Create Power App solution
        app_result = await workflow.create_power_app_solution("Project Tracker")
        logger.info("Power App solution created: %s", json.dumps(app_result, indent=2))
        
        # Example: Migrate SharePoint site
        migration_result = await workflow.migrate_sharepoint_site(
            source_url="http://sharepoint.contoso.local/sites/projects",
            target_url="https://contoso.sharepoint.com/sites/projects"
        )
        logger.info("Migration completed: %s", json.dumps(migration_result, indent=2))
        
        # Example: Deploy SPFx solution
        spfx_result = await workflow.deploy_spfx_solution("solutions/hello-world")
        logger.info("SPFx deployment completed: %s", json.dumps(spfx_result, indent=2))
    
    finally:
        # Cleanup
        await m365_agent.cleanup()
        await sharepoint_dev_agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
