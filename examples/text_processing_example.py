import asyncio
import logging
from datetime import datetime, timedelta

from src.core.base import Task, AgentSystem
from src.agents.text_processor import TextProcessingAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Initialize the agent system
    system = AgentSystem()
    
    # Create and register agents
    text_agent1 = TextProcessingAgent("text_agent_1")
    text_agent2 = TextProcessingAgent("text_agent_2")
    
    system.register_agent(text_agent1)
    system.register_agent(text_agent2)
    
    # Create some example tasks
    tasks = [
        Task(
            task_id="task1",
            task_type="text_analysis",
            priority=1,
            input_data="Hello world! This is an example text for analysis.",
            parameters={},
            deadline=datetime.now() + timedelta(seconds=10)
        ),
        Task(
            task_id="task2",
            task_type="text_transformation",
            priority=2,
            input_data="Transform this text please",
            parameters={"to_upper": True, "reverse": True},
            deadline=datetime.now() + timedelta(seconds=10)
        )
    ]
    
    # Submit tasks
    for task in tasks:
        system.submit_task(task)
    
    # Process tasks
    processor = asyncio.create_task(system.process_tasks())
    
    # Wait for tasks to complete
    await asyncio.sleep(2)
    
    # Check results
    for task in tasks:
        result = system.get_task_result(task.task_id)
        if result:
            logger.info(f"\nTask {task.task_id} result:")
            logger.info(f"Status: {result.status}")
            logger.info(f"Output: {result.output}")
            logger.info(f"Processing time: {result.processing_time:.2f} seconds")
            logger.info(f"Processed by: {result.agent_id}")
            if result.error:
                logger.error(f"Error: {result.error}")
        else:
            logger.warning(f"No result found for task {task.task_id}")
    
    # Cancel the processor task
    processor.cancel()
    try:
        await processor
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    asyncio.run(main())
