import pytest
import asyncio
from unittest.mock import MagicMock, patch
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.agents.cloud_devops_agent import CloudDevOpsAgent

@pytest.fixture
def mock_azure_credentials():
    return MagicMock()

@pytest.fixture
def mock_resource_client():
    client = MagicMock()
    client.resource_groups.check_existence.return_value = False
    return client

@pytest.fixture
def mock_compute_client():
    return MagicMock()

@pytest.fixture
def mock_network_client():
    return MagicMock()

@pytest.fixture
def mock_monitor_client():
    return MagicMock()

@pytest.fixture
def mock_azure_devops_connection():
    return MagicMock()

@pytest.fixture
def config():
    return {
        "azure": {
            "subscription_id": "test-subscription",
            "location": "westus2"
        },
        "azure_devops": {
            "organization_url": "https://dev.azure.com/test-org",
            "project": "test-project",
            "pat": "test-pat"
        }
    }

@pytest.fixture
def agent(
    mock_azure_credentials,
    mock_resource_client,
    mock_compute_client,
    mock_network_client,
    mock_monitor_client,
    mock_azure_devops_connection,
    tmp_path
):
    # Write test config
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump({
            "azure": {
                "subscription_id": "test-subscription"
            },
            "azure_devops": {
                "pat": "test-pat",
                "organization_url": "https://dev.azure.com/test-org"
            }
        }, f)
    
    with patch("azure.mgmt.resource.ResourceManagementClient") as resource_mock, \
         patch("azure.mgmt.compute.ComputeManagementClient") as compute_mock, \
         patch("azure.mgmt.network.NetworkManagementClient") as network_mock, \
         patch("azure.mgmt.monitor.MonitorManagementClient") as monitor_mock, \
         patch("azure.devops.connection.Connection") as connection_mock:
        
        resource_mock.return_value = mock_resource_client
        compute_mock.return_value = mock_compute_client
        network_mock.return_value = mock_network_client
        monitor_mock.return_value = mock_monitor_client
        connection_mock.return_value = mock_azure_devops_connection
        
        agent = CloudDevOpsAgent(
            config_path=str(config_path),
            credentials=mock_azure_credentials,
            work_dir=str(tmp_path / "work")
        )
        
        return agent

@pytest.mark.asyncio
async def test_create_infrastructure(agent, mock_resource_client):
    # Arrange
    template_path = "test_template.json"
    parameters = {
        "resource_group_name": "test-rg",
        "location": "westus2"
    }
    
    with open(template_path, "w") as f:
        json.dump({"resources": []}, f)
    
    mock_deployment = MagicMock()
    mock_deployment.properties.outputs = {"test": "output"}
    mock_resource_client.deployments.begin_create_or_update.return_value.result.return_value = mock_deployment
    
    # Act
    result = await agent.create_infrastructure(template_path, parameters)
    
    # Assert
    assert result == {"test": "output"}
    mock_resource_client.resource_groups.create_or_update.assert_called_once()
    mock_resource_client.deployments.begin_create_or_update.assert_called_once()

@pytest.mark.asyncio
async def test_setup_monitoring(agent):
    # Arrange
    resource_group = "test-rg"
    resource_name = "test-resource"
    
    # Act
    result = await agent.setup_monitoring(resource_group, resource_name)
    
    # Assert
    assert "diagnostic_settings" in result
    assert "alert_rules" in result
    assert result["diagnostic_settings"]["status"] == "created"
    assert result["alert_rules"]["status"] == "created"

@pytest.mark.asyncio
async def test_create_pipeline(agent, mock_azure_devops_connection):
    # Arrange
    pipeline_config = {
        "name": "test-pipeline",
        "repository_id": "test-repo",
        "project_id": "test-project",
        "build_steps": [
            {
                "task": "UsePythonVersion@0",
                "inputs": {
                    "versionSpec": "3.8"
                }
            }
        ],
        "test_steps": [
            {
                "task": "Bash@3",
                "inputs": {
                    "targetType": "inline",
                    "script": "pytest"
                }
            }
        ],
        "deploy_steps": [
            {
                "task": "AzureWebAppContainer@1",
                "inputs": {
                    "azureSubscription": "$(azureSubscription)",
                    "appName": "$(webAppName)"
                }
            }
        ]
    }
    
    mock_pipeline = MagicMock()
    mock_pipeline.id = "test-id"
    mock_pipeline.name = "test-pipeline"
    mock_pipeline.url = "https://dev.azure.com/test-org/test-project/_build/definition?id=1"
    
    mock_azure_devops_connection.get_build_client().create_definition.return_value = mock_pipeline
    
    # Act
    result = await agent.create_pipeline(pipeline_config)
    
    # Assert
    assert result["id"] == "test-id"
    assert result["name"] == "test-pipeline"
    assert result["url"] == "https://dev.azure.com/test-org/test-project/_build/definition?id=1"

@pytest.mark.asyncio
async def test_optimize_resources(agent, mock_compute_client, mock_monitor_client):
    # Arrange
    resource_group = "test-rg"
    
    mock_vm = MagicMock()
    mock_vm.id = "test-vm-id"
    mock_compute_client.virtual_machines.list.return_value = [mock_vm]
    
    mock_metrics = MagicMock()
    mock_metrics.timeseries = [MagicMock()]
    mock_metrics.timeseries[0].data = [MagicMock()]
    mock_metrics.timeseries[0].data[0].average = 10
    
    mock_monitor_client.metrics.list.return_value = [mock_metrics]
    
    # Act
    result = await agent.optimize_resources(resource_group)
    
    # Assert
    assert "recommendations" in result
    assert len(result["recommendations"]) > 0
    assert "estimated_savings" in result

@pytest.mark.asyncio
async def test_implement_security(agent):
    # Arrange
    resource_group = "test-rg"
    
    # Act
    result = await agent.implement_security(resource_group)
    
    # Assert
    assert "security_measures" in result
    assert "compliance_status" in result
    assert result["compliance_status"]["status"] == "compliant"

def test_analyze_metric(agent):
    # Arrange
    mock_metric = MagicMock()
    mock_metric.name.value = "test-metric"
    mock_metric.timeseries = [MagicMock()]
    mock_metric.timeseries[0].data = [
        MagicMock(average=10),
        MagicMock(average=20),
        MagicMock(average=30)
    ]
    
    metrics = [mock_metric]
    
    # Act
    result = agent._analyze_metric(metrics, "test-metric")
    
    # Assert
    assert result["average"] == 20
    assert result["max"] == 30
    assert result["min"] == 10

def test_calculate_savings(agent):
    # Arrange
    recommendations = [
        {
            "type": "Downsize",
            "potential_savings": "30%"
        },
        {
            "type": "Downsize",
            "potential_savings": "20%"
        },
        {
            "type": "Upgrade",
            "impact": "Performance improvement"
        }
    ]
    
    # Act
    result = agent._calculate_savings(recommendations)
    
    # Assert
    assert result == 0.5  # 30% + 20% = 50%
