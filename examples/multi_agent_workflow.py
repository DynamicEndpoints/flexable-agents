import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd
import json
from pathlib import Path

from src.core.base import Task, AgentSystem
from src.agents.data_processor import DataProcessingAgent
from src.agents.api_agent import APIAgent
from src.agents.file_processor import FileProcessingAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Initialize the agent system
    system = AgentSystem()
    
    # Create work directory
    work_dir = Path("work_files")
    work_dir.mkdir(exist_ok=True)
    
    # Create and register agents
    data_agent = DataProcessingAgent("data_agent_1")
    api_agent = APIAgent(
        "api_agent_1",
        base_url="https://api.example.com",
        api_key="your_api_key"
    )
    file_agent = FileProcessingAgent("file_agent_1", str(work_dir))
    
    system.register_agent(data_agent)
    system.register_agent(api_agent)
    system.register_agent(file_agent)
    
    # Example workflow: 
    # 1. Read data file
    # 2. Process and analyze data
    # 3. Send results to API
    # 4. Save results locally
    
    # Step 1: Read data file
    read_task = Task(
        task_id="read_data",
        task_type="file_read",
        priority=1,
        input_data="sample_data.csv",
        parameters={"file_type": "csv"},
        deadline=datetime.now() + timedelta(seconds=30)
    )
    
    system.submit_task(read_task)
    
    # Wait for file read to complete
    while not system.get_task_result("read_data"):
        await asyncio.sleep(0.1)
    
    file_result = system.get_task_result("read_data")
    if file_result.status == "failed":
        logger.error(f"Failed to read file: {file_result.error}")
        return
        
    # Step 2: Process and analyze data
    data = pd.DataFrame(file_result.output)
    
    analysis_task = Task(
        task_id="analyze_data",
        task_type="data_analysis",
        priority=2,
        input_data=data,
        parameters={},
        deadline=datetime.now() + timedelta(seconds=30)
    )
    
    system.submit_task(analysis_task)
    
    # Wait for analysis to complete
    while not system.get_task_result("analyze_data"):
        await asyncio.sleep(0.1)
        
    analysis_result = system.get_task_result("analyze_data")
    if analysis_result.status == "failed":
        logger.error(f"Failed to analyze data: {analysis_result.error}")
        return
        
    # Step 3: Send results to API
    api_task = Task(
        task_id="send_results",
        task_type="api_post",
        priority=3,
        input_data="analysis/results",
        parameters={"data": analysis_result.output},
        deadline=datetime.now() + timedelta(seconds=30)
    )
    
    system.submit_task(api_task)
    
    # Wait for API call to complete
    while not system.get_task_result("send_results"):
        await asyncio.sleep(0.1)
        
    api_result = system.get_task_result("send_results")
    if api_result.status == "failed":
        logger.error(f"Failed to send results to API: {api_result.error}")
        
    # Step 4: Save results locally
    save_task = Task(
        task_id="save_results",
        task_type="file_write",
        priority=4,
        input_data=analysis_result.output,
        parameters={
            "file_path": str(work_dir / "analysis_results.json"),
            "file_type": "json"
        },
        deadline=datetime.now() + timedelta(seconds=30)
    )
    
    system.submit_task(save_task)
    
    # Wait for save to complete
    while not system.get_task_result("save_results"):
        await asyncio.sleep(0.1)
        
    save_result = system.get_task_result("save_results")
    if save_result.status == "failed":
        logger.error(f"Failed to save results: {save_result.error}")
        return
        
    # Print final status
    logger.info("\nWorkflow completed!")
    logger.info("Results:")
    logger.info(f"- Data analysis: {analysis_result.status}")
    logger.info(f"- API submission: {api_result.status}")
    logger.info(f"- Results saved: {save_result.status}")
    
    # Cleanup
    if hasattr(api_agent, 'cleanup'):
        await api_agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
