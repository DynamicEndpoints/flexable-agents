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

class SecurityAuditWorkflow:
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
        
        self.work_dir = Path("work_files/security_audit")
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    async def run_user_audit(self) -> Dict[str, Any]:
        """Run comprehensive user security audit"""
        results = {}
        
        # 1. Check inactive accounts
        if "inactive_accounts" in self.config["components"]["user_audit"]["checks"]:
            inactive_threshold = datetime.now() - timedelta(
                days=self.config["components"]["user_audit"]["thresholds"]["inactive_days"]
            )
            
            inactive_users = await self.m365_agent.process_task(Task(
                task_type="user_management",
                input_data={
                    "action": "list_users",
                    "filter": f"signInActivity/lastSignInDateTime le {inactive_threshold.isoformat()}"
                }
            ))
            results["inactive_accounts"] = inactive_users.output
        
        # 2. Check MFA status
        if "mfa_status" in self.config["components"]["user_audit"]["checks"]:
            mfa_status = await self.m365_agent.process_task(Task(
                task_type="security_management",
                input_data={
                    "action": "get_mfa_status",
                    "filter": "userType eq 'Member'"
                }
            ))
            results["mfa_status"] = mfa_status.output
        
        # 3. Check admin accounts
        if "admin_accounts" in self.config["components"]["user_audit"]["checks"]:
            admin_accounts = await self.m365_agent.process_task(Task(
                task_type="user_management",
                input_data={
                    "action": "list_users",
                    "filter": "assignedRoles/$count gt 0"
                }
            ))
            results["admin_accounts"] = admin_accounts.output
        
        return results
    
    async def run_device_audit(self) -> Dict[str, Any]:
        """Run comprehensive device security audit"""
        results = {}
        
        # 1. Check device compliance
        if "compliance_status" in self.config["components"]["device_audit"]["checks"]:
            compliance_status = await self.intune_agent.process_task(Task(
                task_type="compliance_management",
                input_data={
                    "action": "get_noncompliant_devices"
                }
            ))
            results["compliance_status"] = compliance_status.output
        
        # 2. Check encryption status
        if "encryption_status" in self.config["components"]["device_audit"]["checks"]:
            encryption_status = await self.intune_agent.process_task(Task(
                task_type="device_management",
                input_data={
                    "action": "get_devices",
                    "filter": "deviceEncryptionStatus ne 'Encrypted'"
                }
            ))
            results["encryption_status"] = encryption_status.output
        
        return results
    
    async def run_data_audit(self) -> Dict[str, Any]:
        """Run comprehensive data security audit"""
        results = {}
        
        # 1. Check external sharing
        if "external_sharing" in self.config["components"]["data_audit"]["checks"]:
            sharing_status = await self.m365_agent.process_task(Task(
                task_type="security_management",
                input_data={
                    "action": "get_external_sharing",
                    "period": "D30"
                }
            ))
            results["external_sharing"] = sharing_status.output
        
        # 2. Check DLP violations
        if "dlp_violations" in self.config["components"]["data_audit"]["checks"]:
            dlp_violations = await self.m365_agent.process_task(Task(
                task_type="security_management",
                input_data={
                    "action": "get_dlp_violations",
                    "period": "D30"
                }
            ))
            results["dlp_violations"] = dlp_violations.output
        
        return results
    
    def generate_report(self, audit_results: Dict[str, Any]) -> str:
        """Generate comprehensive security audit report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.work_dir / f"security_audit_{timestamp}.pdf"
        
        # Convert results to pandas DataFrames for analysis
        dfs = {}
        
        # Process user audit results
        if "inactive_accounts" in audit_results.get("user_audit", {}):
            dfs["inactive_users"] = pd.DataFrame(audit_results["user_audit"]["inactive_accounts"])
        
        if "mfa_status" in audit_results.get("user_audit", {}):
            dfs["mfa_status"] = pd.DataFrame(audit_results["user_audit"]["mfa_status"])
        
        # Process device audit results
        if "compliance_status" in audit_results.get("device_audit", {}):
            dfs["noncompliant_devices"] = pd.DataFrame(audit_results["device_audit"]["compliance_status"])
        
        # Generate visualizations and save report
        # (This would use a reporting library like reportlab or python-pptx)
        
        return str(report_path)
    
    async def send_notifications(self, audit_results: Dict[str, Any]):
        """Send notifications based on audit results"""
        if not self.config["notifications"]["email"]["enabled"]:
            return
        
        # Calculate severity based on findings
        severity = self._calculate_severity(audit_results)
        
        if severity in self.config["notifications"]["email"]["severity_levels"]:
            # Send email notification
            await self.exchange_agent.process_task(Task(
                task_type="mail_flow_management",
                input_data={
                    "action": "send_mail",
                    "settings": {
                        "to": self.config["notifications"]["email"]["recipients"],
                        "subject": f"Security Audit Report - {severity.upper()} Issues Found",
                        "body": self._generate_notification_body(audit_results)
                    }
                }
            ))
    
    async def auto_remediate(self, audit_results: Dict[str, Any]):
        """Automatically remediate issues based on configuration"""
        if not self.config["remediation"]["auto_remediate"]["enabled"]:
            return
        
        remediation_actions = self.config["remediation"]["auto_remediate"]["actions"]
        
        # Handle inactive accounts
        if "disable_inactive_accounts" in remediation_actions:
            inactive_accounts = audit_results.get("user_audit", {}).get("inactive_accounts", [])
            for account in inactive_accounts:
                await self.m365_agent.process_task(Task(
                    task_type="user_management",
                    input_data={
                        "action": "update_user",
                        "user_id": account["id"],
                        "properties": {
                            "accountEnabled": False
                        }
                    }
                ))
        
        # Enforce MFA
        if "enforce_mfa" in remediation_actions:
            mfa_status = audit_results.get("user_audit", {}).get("mfa_status", [])
            for user in mfa_status:
                if not user["isMfaEnabled"]:
                    await self.m365_agent.process_task(Task(
                        task_type="security_management",
                        input_data={
                            "action": "enforce_mfa",
                            "user_id": user["id"]
                        }
                    ))
    
    def _calculate_severity(self, audit_results: Dict[str, Any]) -> str:
        """Calculate overall severity of audit findings"""
        severity_score = 0
        
        # Check inactive admin accounts
        admin_accounts = audit_results.get("user_audit", {}).get("admin_accounts", [])
        inactive_admins = [a for a in admin_accounts if a.get("isInactive")]
        if inactive_admins:
            severity_score += 3
        
        # Check MFA status
        mfa_status = audit_results.get("user_audit", {}).get("mfa_status", [])
        users_without_mfa = [u for u in mfa_status if not u.get("isMfaEnabled")]
        if len(users_without_mfa) > 10:
            severity_score += 3
        elif users_without_mfa:
            severity_score += 2
        
        # Check device compliance
        noncompliant_devices = audit_results.get("device_audit", {}).get("compliance_status", [])
        if len(noncompliant_devices) > 20:
            severity_score += 3
        elif noncompliant_devices:
            severity_score += 1
        
        if severity_score >= 5:
            return "critical"
        elif severity_score >= 3:
            return "high"
        elif severity_score >= 1:
            return "medium"
        return "low"
    
    def _generate_notification_body(self, audit_results: Dict[str, Any]) -> str:
        """Generate notification email body"""
        sections = []
        
        # Add user audit findings
        if "user_audit" in audit_results:
            user_audit = audit_results["user_audit"]
            sections.append("User Audit Findings:")
            if "inactive_accounts" in user_audit:
                sections.append(f"- {len(user_audit['inactive_accounts'])} inactive accounts found")
            if "admin_accounts" in user_audit:
                sections.append(f"- {len(user_audit['admin_accounts'])} admin accounts found")
        
        # Add device audit findings
        if "device_audit" in audit_results:
            device_audit = audit_results["device_audit"]
            sections.append("\nDevice Audit Findings:")
            if "compliance_status" in device_audit:
                sections.append(f"- {len(device_audit['compliance_status'])} non-compliant devices found")
        
        # Add data audit findings
        if "data_audit" in audit_results:
            data_audit = audit_results["data_audit"]
            sections.append("\nData Audit Findings:")
            if "dlp_violations" in data_audit:
                sections.append(f"- {len(data_audit['dlp_violations'])} DLP violations found")
        
        return "\n".join(sections)
    
    async def run(self):
        """Run the complete security audit workflow"""
        try:
            logger.info("Starting security audit workflow")
            
            # Run audits
            audit_results = {
                "user_audit": await self.run_user_audit(),
                "device_audit": await self.run_device_audit(),
                "data_audit": await self.run_data_audit()
            }
            
            # Generate report
            report_path = self.generate_report(audit_results)
            logger.info(f"Generated audit report: {report_path}")
            
            # Send notifications
            await self.send_notifications(audit_results)
            
            # Auto-remediate issues
            await self.auto_remediate(audit_results)
            
            logger.info("Security audit workflow completed successfully")
            return {
                "status": "success",
                "report_path": report_path,
                "audit_results": audit_results
            }
        
        except Exception as e:
            logger.error(f"Error in security audit workflow: {str(e)}")
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
    workflow = SecurityAuditWorkflow(
        m365_agent=m365_agent,
        intune_agent=intune_agent,
        exchange_agent=exchange_agent,
        teams_agent=teams_agent,
        config_path="config/templates/workflow_templates/security_audit_workflow.json"
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
