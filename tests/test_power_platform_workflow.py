import pytest
import asyncio
from unittest.mock import MagicMock, patch
import json
from pathlib import Path

from src.agents.m365_admin_agent import M365AdminAgent
from src.agents.sharepoint_dev_agent import SharePointDevAgent
from examples.power_platform_workflow import PowerPlatformWorkflow
from src.core.base import Task, TaskResult

@pytest.fixture
def mock_m365_agent():
    agent = MagicMock(spec=M365AdminAgent)
    agent.process_task = MagicMock()
    return agent

@pytest.fixture
def mock_sharepoint_dev_agent():
    agent = MagicMock(spec=SharePointDevAgent)
    agent.process_task = MagicMock()
    return agent

@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent / "config/templates/sharepoint_dev_config_template.json"
    with open(config_path) as f:
        return json.load(f)

@pytest.fixture
def workflow(mock_m365_agent, mock_sharepoint_dev_agent, config):
    return PowerPlatformWorkflow(
        m365_agent=mock_m365_agent,
        sharepoint_dev_agent=mock_sharepoint_dev_agent,
        config_path=str(Path(__file__).parent.parent / "config/templates/sharepoint_dev_config_template.json")
    )

@pytest.mark.asyncio
async def test_create_business_solution(workflow, mock_sharepoint_dev_agent):
    # Arrange
    solution_name = "TestSolution"
    mock_sharepoint_dev_agent.process_task.side_effect = [
        TaskResult(task_id="1", status="success", output={"lists": ["Projects", "Tasks"]}, agent_id="test"),
        TaskResult(task_id="2", status="success", output={"app_id": "test_app"}, agent_id="test"),
        TaskResult(task_id="3", status="success", output={"flows": ["approval", "notification"]}, agent_id="test"),
        TaskResult(task_id="4", status="success", output={"report_id": "test_report"}, agent_id="test")
    ]
    
    # Act
    result = await workflow.create_business_solution(solution_name)
    
    # Assert
    assert "sharepoint_lists" in result
    assert "power_app" in result
    assert "power_automate_flows" in result
    assert "power_bi_report" in result
    assert mock_sharepoint_dev_agent.process_task.call_count == 4

@pytest.mark.asyncio
async def test_deploy_solution(workflow, mock_sharepoint_dev_agent):
    # Arrange
    solution_name = "TestSolution"
    environment = "prod"
    mock_sharepoint_dev_agent.process_task.side_effect = [
        TaskResult(task_id="1", status="success", output={"solution_path": "test.zip"}, agent_id="test"),
        TaskResult(task_id="2", status="success", output={"status": "success"}, agent_id="test")
    ]
    
    # Act
    result = await workflow.deploy_solution(solution_name, environment)
    
    # Assert
    assert "export" in result
    assert "import" in result
    assert mock_sharepoint_dev_agent.process_task.call_count == 2

@pytest.mark.asyncio
async def test_create_business_solution_error(workflow, mock_sharepoint_dev_agent):
    # Arrange
    solution_name = "TestSolution"
    mock_sharepoint_dev_agent.process_task.side_effect = Exception("Test error")
    
    # Act/Assert
    with pytest.raises(Exception):
        await workflow.create_business_solution(solution_name)

@pytest.mark.asyncio
async def test_deploy_solution_error(workflow, mock_sharepoint_dev_agent):
    # Arrange
    solution_name = "TestSolution"
    environment = "prod"
    mock_sharepoint_dev_agent.process_task.side_effect = Exception("Test error")
    
    # Act/Assert
    with pytest.raises(Exception):
        await workflow.deploy_solution(solution_name, environment)

@pytest.mark.asyncio
async def test_create_business_solution_validation(workflow, mock_sharepoint_dev_agent):
    # Arrange
    solution_name = ""  # Invalid solution name
    
    # Act/Assert
    with pytest.raises(ValueError):
        await workflow.create_business_solution(solution_name)

@pytest.mark.asyncio
async def test_deploy_solution_validation(workflow, mock_sharepoint_dev_agent):
    # Arrange
    solution_name = "TestSolution"
    environment = "invalid"  # Invalid environment
    
    # Act/Assert
    with pytest.raises(ValueError):
        await workflow.deploy_solution(solution_name, environment)

@pytest.mark.asyncio
async def test_power_bi_report_creation(workflow, mock_sharepoint_dev_agent):
    # Arrange
    solution_name = "TestSolution"
    mock_sharepoint_dev_agent.process_task.side_effect = [
        TaskResult(task_id="1", status="success", output={"lists": ["Projects", "Tasks"]}, agent_id="test"),
        TaskResult(task_id="2", status="success", output={"app_id": "test_app"}, agent_id="test"),
        TaskResult(task_id="3", status="success", output={"flows": ["approval", "notification"]}, agent_id="test"),
        TaskResult(task_id="4", status="success", output={
            "report_id": "test_report",
            "pages": ["Project Overview", "Task Analysis"],
            "refreshSchedule": "daily"
        }, agent_id="test")
    ]
    
    # Act
    result = await workflow.create_business_solution(solution_name)
    
    # Assert
    assert "power_bi_report" in result
    assert result["power_bi_report"]["pages"] == ["Project Overview", "Task Analysis"]
    assert result["power_bi_report"]["refreshSchedule"] == "daily"

@pytest.mark.asyncio
async def test_solution_cleanup(workflow, mock_m365_agent, mock_sharepoint_dev_agent):
    # Act
    await workflow.cleanup()
    
    # Assert
    mock_m365_agent.cleanup.assert_called_once()
    mock_sharepoint_dev_agent.cleanup.assert_called_once()
