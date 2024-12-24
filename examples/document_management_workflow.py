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

class DocumentManagementWorkflow:
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
        
        self.work_dir = Path("work_files/document_management")
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_document_center(self, center_name: str) -> Dict[str, Any]:
        """Create a document management center"""
        results = {}
        
        # 1. Create document center site
        logger.info("Creating document center site")
        site_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "create_site",
                "site_name": center_name,
                "site_alias": center_name.lower().replace(" ", "-"),
                "template": "DocumentCenter",
                "features": {
                    "document_id": True,
                    "content_organizer": True,
                    "document_sets": True,
                    "in_place_records": True
                }
            }
        ))
        results["site"] = site_result.output
        
        # 2. Create content types
        logger.info("Creating content types")
        content_types_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="information_architecture",
            input_data={
                "action": "create_content_types",
                "site_id": site_result.output["id"],
                "content_types": [
                    {
                        "name": "Contract Document",
                        "description": "Legal contracts and agreements",
                        "fields": [
                            {"name": "ContractNumber", "type": "Text", "required": True},
                            {"name": "ContractType", "type": "Choice", "choices": ["Service", "License", "NDA"]},
                            {"name": "EffectiveDate", "type": "DateTime"},
                            {"name": "ExpirationDate", "type": "DateTime"},
                            {"name": "ContractValue", "type": "Currency"},
                            {"name": "ContractStatus", "type": "Choice", "choices": ["Draft", "In Review", "Active", "Expired"]}
                        ]
                    },
                    {
                        "name": "Policy Document",
                        "description": "Company policies and procedures",
                        "fields": [
                            {"name": "PolicyNumber", "type": "Text", "required": True},
                            {"name": "Department", "type": "Choice", "choices": ["HR", "IT", "Finance", "Legal"]},
                            {"name": "ReviewDate", "type": "DateTime"},
                            {"name": "NextReviewDate", "type": "DateTime"},
                            {"name": "PolicyStatus", "type": "Choice", "choices": ["Draft", "Under Review", "Active", "Archived"]}
                        ]
                    }
                ]
            }
        ))
        results["content_types"] = content_types_result.output
        
        # 3. Create document libraries
        logger.info("Creating document libraries")
        libraries_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "create_libraries",
                "site_id": site_result.output["id"],
                "libraries": [
                    {
                        "name": "Contracts",
                        "content_types": ["Contract Document"],
                        "versioning": True,
                        "require_checkout": True,
                        "folders": [
                            "Service Agreements",
                            "License Agreements",
                            "NDAs"
                        ]
                    },
                    {
                        "name": "Policies",
                        "content_types": ["Policy Document"],
                        "versioning": True,
                        "require_checkout": True,
                        "folders": [
                            "HR Policies",
                            "IT Policies",
                            "Finance Policies",
                            "Legal Policies"
                        ]
                    }
                ]
            }
        ))
        results["libraries"] = libraries_result.output
        
        # 4. Configure retention policies
        logger.info("Configuring retention policies")
        retention_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="information_architecture",
            input_data={
                "action": "configure_retention",
                "site_id": site_result.output["id"],
                "policies": [
                    {
                        "name": "Contract Retention",
                        "library": "Contracts",
                        "duration": "7years",
                        "trigger": "after_expiration_date",
                        "action": "delete"
                    },
                    {
                        "name": "Policy Retention",
                        "library": "Policies",
                        "duration": "5years",
                        "trigger": "after_next_review_date",
                        "action": "archive"
                    }
                ]
            }
        ))
        results["retention"] = retention_result.output
        
        # 5. Create Power Automate flows
        logger.info("Creating automation flows")
        flows_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="power_automate_development",
            input_data={
                "action": "create_flow",
                "flows": [
                    {
                        "name": "Contract Review Reminder",
                        "trigger": {
                            "type": "schedule",
                            "frequency": "daily"
                        },
                        "actions": [
                            {
                                "type": "get_items",
                                "library": "Contracts",
                                "filter": "ExpirationDate le dateadd(days, 30, utcnow())"
                            },
                            {
                                "type": "apply_to_each",
                                "actions": [
                                    {
                                        "type": "send_email",
                                        "to": "@{item.Owner}",
                                        "subject": "Contract Review Required",
                                        "body": "Contract @{item.ContractNumber} expires in @{days(item.ExpirationDate, utcnow())} days"
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "Policy Review Workflow",
                        "trigger": {
                            "type": "item_created_modified",
                            "library": "Policies"
                        },
                        "actions": [
                            {
                                "type": "start_approval",
                                "approvers": ["@{item.Department}Manager"],
                                "settings": {
                                    "approval_type": "content_approval",
                                    "outcome_actions": {
                                        "approved": [
                                            {
                                                "type": "update_item",
                                                "field": "PolicyStatus",
                                                "value": "Active"
                                            }
                                        ],
                                        "rejected": [
                                            {
                                                "type": "update_item",
                                                "field": "PolicyStatus",
                                                "value": "Draft"
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ))
        results["flows"] = flows_result.output
        
        # 6. Configure search settings
        logger.info("Configuring search settings")
        search_result = await self.sharepoint_dev_agent.process_task(Task(
            task_type="sharepoint_development",
            input_data={
                "action": "configure_search",
                "site_id": site_result.output["id"],
                "settings": {
                    "managed_properties": [
                        {"name": "ContractNumber", "type": "Text", "searchable": True},
                        {"name": "PolicyNumber", "type": "Text", "searchable": True},
                        {"name": "Department", "type": "Text", "searchable": True, "refinable": True},
                        {"name": "ContractType", "type": "Text", "searchable": True, "refinable": True}
                    ],
                    "result_sources": [
                        {
                            "name": "Contracts",
                            "query": "ContentType:Contract Document"
                        },
                        {
                            "name": "Policies",
                            "query": "ContentType:Policy Document"
                        }
                    ]
                }
            }
        ))
        results["search"] = search_result.output
        
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
    workflow = DocumentManagementWorkflow(
        m365_agent=m365_agent,
        sharepoint_dev_agent=sharepoint_dev_agent,
        config_path="config/templates/sharepoint_dev_config_template.json"
    )
    
    try:
        # Create document center
        result = await workflow.create_document_center("Corporate Documents")
        logger.info("Document center created: %s", json.dumps(result, indent=2))
    
    finally:
        # Cleanup
        await m365_agent.cleanup()
        await sharepoint_dev_agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
