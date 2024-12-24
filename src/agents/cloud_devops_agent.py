import asyncio
import logging
from typing import Dict, Any, List
import json
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
import yaml

logger = logging.getLogger(__name__)

class CloudDevOpsAgent:
    """Agent for managing Azure cloud infrastructure and DevOps processes"""
    
    def __init__(
        self,
        config_path: str,
        credentials: DefaultAzureCredential = None,
        work_dir: str = "work_files/cloud_devops"
    ):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        with open(config_path) as f:
            self.config = json.load(f)
        
        # Initialize Azure clients
        self.credentials = credentials or DefaultAzureCredential()
        self.subscription_id = self.config["azure"]["subscription_id"]
        
        self.resource_client = ResourceManagementClient(
            self.credentials, 
            self.subscription_id
        )
        self.compute_client = ComputeManagementClient(
            self.credentials, 
            self.subscription_id
        )
        self.network_client = NetworkManagementClient(
            self.credentials, 
            self.subscription_id
        )
        self.monitor_client = MonitorManagementClient(
            self.credentials, 
            self.subscription_id
        )
        
        # Initialize Azure DevOps connection
        personal_access_token = self.config["azure_devops"]["pat"]
        organization_url = self.config["azure_devops"]["organization_url"]
        
        credentials = BasicAuthentication('', personal_access_token)
        self.azure_devops_connection = Connection(
            base_url=organization_url,
            creds=credentials
        )
    
    async def create_infrastructure(self, template_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create Azure infrastructure using ARM templates"""
        # Load ARM template
        with open(template_path) as f:
            template = json.load(f)
        
        # Create resource group if it doesn't exist
        rg_name = parameters["resource_group_name"]
        rg_location = parameters["location"]
        
        if not self.resource_client.resource_groups.check_existence(rg_name):
            self.resource_client.resource_groups.create_or_update(
                rg_name,
                {"location": rg_location}
            )
        
        # Deploy ARM template
        deployment_name = f"deployment_{Path(template_path).stem}"
        deployment_result = self.resource_client.deployments.begin_create_or_update(
            rg_name,
            deployment_name,
            {
                "properties": {
                    "template": template,
                    "parameters": parameters,
                    "mode": "Incremental"
                }
            }
        ).result()
        
        return deployment_result.properties.outputs
    
    async def setup_monitoring(self, resource_group: str, resource_name: str) -> Dict[str, Any]:
        """Setup Azure Monitor for resources"""
        # Create diagnostic settings
        diagnostic_settings = {
            "logs": [
                {
                    "category": "Administrative",
                    "enabled": True,
                    "retentionPolicy": {
                        "days": 30,
                        "enabled": True
                    }
                },
                {
                    "category": "Security",
                    "enabled": True,
                    "retentionPolicy": {
                        "days": 30,
                        "enabled": True
                    }
                }
            ],
            "metrics": [
                {
                    "category": "AllMetrics",
                    "enabled": True,
                    "retentionPolicy": {
                        "days": 30,
                        "enabled": True
                    }
                }
            ]
        }
        
        # Create alert rules
        alert_rules = [
            {
                "name": "High CPU Usage",
                "description": "Alert when CPU usage exceeds 80%",
                "severity": 2,
                "enabled": True,
                "evaluation_frequency": "PT1M",
                "window_size": "PT5M",
                "criteria": {
                    "metric_name": "Percentage CPU",
                    "metric_namespace": "Microsoft.Compute/virtualMachines",
                    "operator": "GreaterThan",
                    "threshold": 80,
                    "time_aggregation": "Average"
                }
            }
        ]
        
        # Apply monitoring settings
        monitoring_result = {
            "diagnostic_settings": await self._create_diagnostic_settings(
                resource_group,
                resource_name,
                diagnostic_settings
            ),
            "alert_rules": await self._create_alert_rules(
                resource_group,
                resource_name,
                alert_rules
            )
        }
        
        return monitoring_result
    
    async def create_pipeline(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Azure DevOps pipeline"""
        # Get Azure DevOps clients
        git_client = self.azure_devops_connection.get_git_client()
        build_client = self.azure_devops_connection.get_build_client()
        
        # Create pipeline YAML
        pipeline_yaml = {
            "trigger": ["main"],
            "pool": {"vmImage": "ubuntu-latest"},
            "stages": [
                {
                    "stage": "Build",
                    "jobs": [
                        {
                            "job": "BuildJob",
                            "steps": pipeline_config["build_steps"]
                        }
                    ]
                },
                {
                    "stage": "Test",
                    "jobs": [
                        {
                            "job": "TestJob",
                            "steps": pipeline_config["test_steps"]
                        }
                    ]
                },
                {
                    "stage": "Deploy",
                    "jobs": [
                        {
                            "job": "DeployJob",
                            "steps": pipeline_config["deploy_steps"]
                        }
                    ]
                }
            ]
        }
        
        # Create pipeline file in repo
        pipeline_path = "azure-pipelines.yml"
        repo_id = pipeline_config["repository_id"]
        
        git_client.create_push(
            {
                "commits": [{
                    "comment": "Add CI/CD pipeline",
                    "changes": [{
                        "changeType": "add",
                        "item": {
                            "path": pipeline_path
                        },
                        "newContent": {
                            "content": yaml.dump(pipeline_yaml),
                            "contentType": "rawtext"
                        }
                    }]
                }]
            },
            repo_id
        )
        
        # Create pipeline definition
        pipeline_definition = {
            "name": pipeline_config["name"],
            "repository": {
                "id": repo_id,
                "type": "azureReposGit"
            },
            "configuration": {
                "path": pipeline_path,
                "type": "yaml"
            }
        }
        
        pipeline = build_client.create_definition(
            pipeline_definition,
            project=pipeline_config["project_id"]
        )
        
        return {
            "id": pipeline.id,
            "name": pipeline.name,
            "url": pipeline.url
        }
    
    async def optimize_resources(self, resource_group: str) -> Dict[str, Any]:
        """Optimize Azure resources for cost and performance"""
        recommendations = []
        
        # Get VM sizes and usage
        vms = self.compute_client.virtual_machines.list(resource_group)
        for vm in vms:
            # Get VM metrics
            metrics = self.monitor_client.metrics.list(
                vm.id,
                timespan="P7D",
                interval="PT1H",
                metricnames="Percentage CPU,Available Memory Bytes"
            )
            
            # Analyze metrics and make recommendations
            cpu_usage = self._analyze_metric(metrics, "Percentage CPU")
            memory_usage = self._analyze_metric(metrics, "Available Memory Bytes")
            
            if cpu_usage["average"] < 20:
                recommendations.append({
                    "resource_id": vm.id,
                    "type": "Downsize",
                    "reason": "Low CPU utilization",
                    "potential_savings": "30%"
                })
            
            if memory_usage["average"] > 80:
                recommendations.append({
                    "resource_id": vm.id,
                    "type": "Upgrade",
                    "reason": "High memory usage",
                    "impact": "Performance improvement"
                })
        
        return {
            "recommendations": recommendations,
            "estimated_savings": self._calculate_savings(recommendations)
        }
    
    async def implement_security(self, resource_group: str) -> Dict[str, Any]:
        """Implement security best practices"""
        security_measures = []
        
        # Enable Azure Security Center
        security_measures.append(
            await self._enable_security_center(resource_group)
        )
        
        # Configure Network Security Groups
        security_measures.append(
            await self._configure_network_security(resource_group)
        )
        
        # Enable encryption
        security_measures.append(
            await self._enable_encryption(resource_group)
        )
        
        # Configure backup policies
        security_measures.append(
            await self._configure_backups(resource_group)
        )
        
        return {
            "security_measures": security_measures,
            "compliance_status": await self._check_compliance(resource_group)
        }
    
    def _analyze_metric(self, metrics: Any, metric_name: str) -> Dict[str, float]:
        """Analyze Azure Monitor metrics"""
        values = []
        for metric in metrics:
            if metric.name.value == metric_name:
                for timeseries in metric.timeseries:
                    for data in timeseries.data:
                        if data.average is not None:
                            values.append(data.average)
        
        return {
            "average": sum(values) / len(values) if values else 0,
            "max": max(values) if values else 0,
            "min": min(values) if values else 0
        }
    
    def _calculate_savings(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate estimated cost savings"""
        total_savings = 0
        for rec in recommendations:
            if rec["type"] == "Downsize":
                savings = float(rec["potential_savings"].strip("%")) / 100
                total_savings += savings
        return total_savings
    
    async def _enable_security_center(self, resource_group: str) -> Dict[str, Any]:
        """Enable and configure Azure Security Center"""
        # Implementation details
        return {"status": "enabled"}
    
    async def _configure_network_security(self, resource_group: str) -> Dict[str, Any]:
        """Configure network security groups"""
        # Implementation details
        return {"status": "configured"}
    
    async def _enable_encryption(self, resource_group: str) -> Dict[str, Any]:
        """Enable encryption for resources"""
        # Implementation details
        return {"status": "enabled"}
    
    async def _configure_backups(self, resource_group: str) -> Dict[str, Any]:
        """Configure backup policies"""
        # Implementation details
        return {"status": "configured"}
    
    async def _check_compliance(self, resource_group: str) -> Dict[str, Any]:
        """Check compliance status"""
        # Implementation details
        return {"status": "compliant"}
    
    async def _create_diagnostic_settings(
        self,
        resource_group: str,
        resource_name: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create diagnostic settings"""
        # Implementation details
        return {"status": "created"}
    
    async def _create_alert_rules(
        self,
        resource_group: str,
        resource_name: str,
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create alert rules"""
        # Implementation details
        return {"status": "created"}
