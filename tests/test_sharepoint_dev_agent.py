import pytest
import asyncio
from unittest.mock import MagicMock, patch
import json
from pathlib import Path

from src.agents.sharepoint_dev_agent import SharePointDevAgent
from src.core.base import Task, TaskResult

@pytest.fixture
def mock_graph_client():
    client = MagicMock()
    client._make_request = MagicMock()
    return client

@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent / "config/templates/sharepoint_dev_config_template.json"
    with open(config_path) as f:
        return json.load(f)

@pytest.fixture
def agent(mock_graph_client, config):
    return SharePointDevAgent(
        agent_id="test_agent",
        work_dir="test_work_dir",
        graph_client=mock_graph_client,
        config=config
    )

@pytest.mark.asyncio
async def test_create_sharepoint_site(agent, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = {
        "id": "test_site_id",
        "displayName": "Test Site",
        "webUrl": "https://test.sharepoint.com/sites/test"
    }
    
    # Act
    result = await agent.process_task(Task(
        task_type="sharepoint_development",
        input_data={
            "action": "create_site",
            "site_name": "Test Site",
            "site_alias": "test",
            "template": "TeamSite"
        }
    ))
    
    # Assert
    assert result.status == "success"
    assert result.output["displayName"] == "Test Site"
    mock_graph_client._make_request.assert_called_once()

@pytest.mark.asyncio
async def test_create_power_app(agent, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = {
        "id": "test_app_id",
        "displayName": "Test App"
    }
    
    # Act
    result = await agent.process_task(Task(
        task_type="power_apps_development",
        input_data={
            "action": "create_app",
            "app_name": "Test App",
            "environment": "dev",
            "template": "blank"
        }
    ))
    
    # Assert
    assert result.status == "success"
    assert result.output["displayName"] == "Test App"

@pytest.mark.asyncio
async def test_create_flow(agent, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = {
        "id": "test_flow_id",
        "displayName": "Test Flow"
    }
    
    # Act
    result = await agent.process_task(Task(
        task_type="power_automate_development",
        input_data={
            "action": "create_flow",
            "flow_name": "Test Flow",
            "environment": "dev",
            "flow_definition": {
                "triggers": {"manual": {}},
                "actions": {"send_email": {}}
            }
        }
    ))
    
    # Assert
    assert result.status == "success"
    assert result.output["displayName"] == "Test Flow"

@pytest.mark.asyncio
async def test_create_content_type(agent, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = {
        "id": "test_ct_id",
        "name": "Test Content Type"
    }
    
    # Act
    result = await agent.process_task(Task(
        task_type="information_architecture",
        input_data={
            "action": "create_content_type",
            "site_id": "test_site",
            "name": "Test Content Type",
            "fields": [
                {"name": "TestField", "type": "Text"}
            ]
        }
    ))
    
    # Assert
    assert result.status == "success"
    assert result.output["name"] == "Test Content Type"

@pytest.mark.asyncio
async def test_assess_migration_environment(agent, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = {
        "source": {"status": "ready"},
        "target": {"status": "ready"}
    }
    
    # Act
    result = await agent.process_task(Task(
        task_type="migration_management",
        input_data={
            "action": "assess_environment",
            "source": {
                "url": "http://source.sharepoint.com",
                "type": "on_premises"
            },
            "target": {
                "url": "https://target.sharepoint.com",
                "type": "sharepoint_online"
            }
        }
    ))
    
    # Assert
    assert result.status == "success"
    assert result.output["source"]["status"] == "ready"
    assert result.output["target"]["status"] == "ready"

@pytest.mark.asyncio
async def test_execute_migration(agent, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = {
        "status": "completed",
        "items_migrated": 100
    }
    
    # Act
    result = await agent.process_task(Task(
        task_type="migration_management",
        input_data={
            "action": "execute_migration",
            "migration_tool": "ShareGate",
            "source_url": "http://source.sharepoint.com",
            "target_url": "https://target.sharepoint.com",
            "settings": {
                "copy_permissions": True,
                "copy_content": True
            }
        }
    ))
    
    # Assert
    assert result.status == "success"
    assert result.output["status"] == "completed"
    assert result.output["items_migrated"] == 100

@pytest.mark.asyncio
async def test_error_handling(agent):
    # Act
    result = await agent.process_task(Task(
        task_type="unknown_type",
        input_data={}
    ))
    
    # Assert
    assert result.status == "failed"
    assert "Unknown task type" in result.error

@pytest.mark.asyncio
async def test_cleanup(agent):
    # Act
    await agent.cleanup()
    
    # Assert
    # Verify that cleanup doesn't raise any exceptions
    assert True
