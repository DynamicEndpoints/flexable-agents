import asyncio
import logging
from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from src.agents.m365_admin_agent import M365AdminAgent
from src.agents.intune_agent import IntuneAgent
from src.agents.exchange_agent import ExchangeAgent
from src.agents.teams_agent import TeamsAgent
from src.core.base import Task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceMonitoringWorkflow:
    def __init__(
        self,
        m365_agent: M365AdminAgent,
        intune_agent: IntuneAgent,
        exchange_agent: ExchangeAgent,
        teams_agent: TeamsAgent,
        config_path: str
    ):
        self.m365_agent = m365_agent
        self.intune_agent = intune_agent
        self.exchange_agent = exchange_agent
        self.teams_agent = teams_agent
        
        # Load configuration
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.work_dir = Path("work_files/compliance_monitoring")
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    async def scan_data_classification(self) -> Dict[str, Any]:
        """Scan and classify sensitive data across M365 services"""
        results = {}
        
        for location in self.config["components"]["data_classification"]["locations"]:
            if location == "sharepoint":
                # Scan SharePoint sites
                sharepoint_scan = await self.m365_agent.process_task(Task(
                    task_type="security_management",
                    input_data={
                        "action": "scan_sensitive_data",
                        "location": "sharepoint",
                        "scan_types": self.config["components"]["data_classification"]["scan_types"]
                    }
                ))
                results["sharepoint"] = sharepoint_scan.output
            
            elif location == "onedrive":
                # Scan OneDrive
                onedrive_scan = await self.m365_agent.process_task(Task(
                    task_type="security_management",
                    input_data={
                        "action": "scan_sensitive_data",
                        "location": "onedrive",
                        "scan_types": self.config["components"]["data_classification"]["scan_types"]
                    }
                ))
                results["onedrive"] = onedrive_scan.output
        
        return results
    
    async def check_policy_compliance(self) -> Dict[str, Any]:
        """Check compliance with various policies"""
        results = {}
        
        for policy_type in self.config["components"]["policy_compliance"]["policies"]:
            if policy_type == "data_retention":
                # Check retention policy compliance
                retention_check = await self.m365_agent.process_task(Task(
                    task_type="security_management",
                    input_data={
                        "action": "check_retention_compliance"
                    }
                ))
                results["data_retention"] = retention_check.output
            
            elif policy_type == "device_compliance":
                # Check device compliance policies
                device_check = await self.intune_agent.process_task(Task(
                    task_type="compliance_management",
                    input_data={
                        "action": "check_compliance_policies"
                    }
                ))
                results["device_compliance"] = device_check.output
        
        return results
    
    async def review_access(self) -> Dict[str, Any]:
        """Review access permissions and privileges"""
        results = {}
        
        for review_type in self.config["components"]["access_reviews"]["scope"]:
            if review_type == "privileged_roles":
                # Review admin roles
                admin_review = await self.m365_agent.process_task(Task(
                    task_type="security_management",
                    input_data={
                        "action": "review_privileged_access"
                    }
                ))
                results["privileged_roles"] = admin_review.output
            
            elif review_type == "guest_access":
                # Review guest access
                guest_review = await self.m365_agent.process_task(Task(
                    task_type="security_management",
                    input_data={
                        "action": "review_guest_access"
                    }
                ))
                results["guest_access"] = guest_review.output
        
        return results
    
    def generate_report(self, monitoring_results: Dict[str, Any]) -> str:
        """Generate compliance monitoring report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.work_dir / f"compliance_report_{timestamp}.xlsx"
        
        # Create Excel writer
        writer = pd.ExcelWriter(report_path, engine='xlsxwriter')
        
        # Process data classification results
        if "data_classification" in monitoring_results:
            df_classification = pd.DataFrame(monitoring_results["data_classification"])
            df_classification.to_excel(writer, sheet_name='Data Classification', index=False)
        
        # Process policy compliance results
        if "policy_compliance" in monitoring_results:
            df_compliance = pd.DataFrame(monitoring_results["policy_compliance"])
            df_compliance.to_excel(writer, sheet_name='Policy Compliance', index=False)
        
        # Process access review results
        if "access_review" in monitoring_results:
            df_access = pd.DataFrame(monitoring_results["access_review"])
            df_access.to_excel(writer, sheet_name='Access Reviews', index=False)
        
        # Save report
        writer.save()
        return str(report_path)
    
    async def send_alerts(self, monitoring_results: Dict[str, Any]):
        """Send alerts based on monitoring results"""
        if not self.config["alerts"]["email"]["enabled"]:
            return
        
        alerts = []
        
        # Check data classification alerts
        if "data_classification" in monitoring_results:
            for finding in monitoring_results["data_classification"].get("findings", []):
                if finding["sensitivity_level"] in ["confidential", "highly_confidential"]:
                    alerts.append({
                        "severity": "high",
                        "message": f"Sensitive data found: {finding['type']} in {finding['location']}"
                    })
        
        # Check policy compliance alerts
        if "policy_compliance" in monitoring_results:
            for violation in monitoring_results["policy_compliance"].get("violations", []):
                alerts.append({
                    "severity": "high" if violation["critical"] else "medium",
                    "message": f"Policy violation: {violation['policy']} - {violation['details']}"
                })
        
        # Send alerts
        for alert in alerts:
            if alert["severity"] in self.config["alerts"]["email"]["severity_levels"]:
                await self.exchange_agent.process_task(Task(
                    task_type="mail_flow_management",
                    input_data={
                        "action": "send_mail",
                        "settings": {
                            "to": self.config["alerts"]["email"]["recipients"],
                            "subject": f"Compliance Alert - {alert['severity'].upper()}",
                            "body": alert["message"]
                        }
                    }
                ))
    
    async def apply_remediation(self, monitoring_results: Dict[str, Any]):
        """Apply automated remediation actions"""
        if not self.config["automation"]["remediation"]["enabled"]:
            return
        
        # Handle sensitive data remediation
        if (self.config["automation"]["remediation"]["actions"]["quarantine_sensitive_data"]["enabled"] and
            "data_classification" in monitoring_results):
            for finding in monitoring_results["data_classification"].get("findings", []):
                if finding["sensitivity_level"] == self.config["automation"]["remediation"]["actions"]["quarantine_sensitive_data"]["threshold"]:
                    await self.m365_agent.process_task(Task(
                        task_type="security_management",
                        input_data={
                            "action": "quarantine_content",
                            "content_id": finding["id"],
                            "reason": "Automated quarantine of highly sensitive content"
                        }
                    ))
        
        # Handle guest access remediation
        if (self.config["automation"]["remediation"]["actions"]["revoke_guest_access"]["enabled"] and
            "access_review" in monitoring_results):
            for review in monitoring_results["access_review"].get("guest_access", []):
                if any(condition in review["status"] for condition in 
                      self.config["automation"]["remediation"]["actions"]["revoke_guest_access"]["conditions"]):
                    await self.m365_agent.process_task(Task(
                        task_type="user_management",
                        input_data={
                            "action": "revoke_guest_access",
                            "user_id": review["user_id"]
                        }
                    ))
    
    async def run(self):
        """Run the complete compliance monitoring workflow"""
        try:
            logger.info("Starting compliance monitoring workflow")
            
            # Run monitoring tasks
            monitoring_results = {
                "data_classification": await self.scan_data_classification(),
                "policy_compliance": await self.check_policy_compliance(),
                "access_review": await self.review_access()
            }
            
            # Generate report
            report_path = self.generate_report(monitoring_results)
            logger.info(f"Generated compliance report: {report_path}")
            
            # Send alerts
            await self.send_alerts(monitoring_results)
            
            # Apply remediation
            await self.apply_remediation(monitoring_results)
            
            logger.info("Compliance monitoring workflow completed successfully")
            return {
                "status": "success",
                "report_path": report_path,
                "monitoring_results": monitoring_results
            }
        
        except Exception as e:
            logger.error(f"Error in compliance monitoring workflow: {str(e)}")
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
    
    # Initialize workflow
    workflow = ComplianceMonitoringWorkflow(
        m365_agent=m365_agent,
        intune_agent=intune_agent,
        exchange_agent=exchange_agent,
        teams_agent=teams_agent,
        config_path="config/templates/workflow_templates/compliance_workflow.json"
    )
    
    try:
        # Run workflow
        result = await workflow.run()
        logger.info("Workflow completed: %s", json.dumps(result, indent=2))
    
    finally:
        # Cleanup
        await m365_agent.cleanup()
        await intune_agent.cleanup()
        await exchange_agent.cleanup()
        await teams_agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
