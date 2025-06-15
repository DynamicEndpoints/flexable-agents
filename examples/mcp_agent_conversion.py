"""Example of converting existing agents to MCP-compatible agents."""

import asyncio
from typing import Dict, Any
from src.core import (
    Agent, Task, TaskResult, Message,
    mcp_compatible_agent, mcp_tool, create_mcp_tool_metadata,
    EnhancedAgent, register_legacy_agent_tools
)


# Example 1: Converting existing agent with decorator
@mcp_compatible_agent(auto_discover=True)
class ExampleAgent(Agent):
    """Example agent that will be converted to MCP-compatible."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, capabilities=["text_processing", "data_analysis"])
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process a task."""
        if task.task_type == "text_processing":
            result = await self.process_text(task.input_data)
        elif task.task_type == "data_analysis":
            result = await self.analyze_data(task.input_data)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
        
        return TaskResult(
            task_id=task.task_id,
            status="success",
            output=result,
            processing_time=0.1,
            agent_id=self.agent_id
        )
    
    async def handle_message(self, message: Message):
        """Handle a message."""
        return None
    
    @mcp_tool(
        name="process_text",
        description="Process text data with various operations",
        category="text",
        tags=["nlp", "processing"]
    )
    async def process_text(self, text: str, operation: str = "uppercase") -> str:
        """
        Process text with specified operation.
        
        Args:
            text: Input text to process
            operation: Operation to perform (uppercase, lowercase, reverse)
        """
        if operation == "uppercase":
            return text.upper()
        elif operation == "lowercase":
            return text.lower()
        elif operation == "reverse":
            return text[::-1]
        else:
            return text
    
    @mcp_tool(
        name="analyze_data",
        description="Analyze data and return statistics",
        category="analytics",
        tags=["data", "statistics"]
    )
    async def analyze_data(self, data: list) -> Dict[str, Any]:
        """
        Analyze data and return statistics.
        
        Args:
            data: List of numbers to analyze
        """
        if not data:
            return {"error": "No data provided"}
        
        return {
            "count": len(data),
            "sum": sum(data),
            "average": sum(data) / len(data),
            "min": min(data),
            "max": max(data)
        }


# Example 2: Manual conversion of existing agent
class LegacyAgent(Agent):
    """Legacy agent without MCP decorators."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, capabilities=["legacy_task"])
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process legacy task."""
        result = await self.legacy_method(task.input_data)
        return TaskResult(
            task_id=task.task_id,
            status="success",
            output=result,
            processing_time=0.1,
            agent_id=self.agent_id
        )
    
    async def handle_message(self, message: Message):
        """Handle message."""
        return None
    
    async def legacy_method(self, data: str) -> str:
        """Legacy method to be converted to MCP tool."""
        return f"Processed: {data}"
    
    def another_legacy_method(self, value: int) -> int:
        """Another legacy method."""
        return value * 2


def convert_legacy_agent_example():
    """Example of manually converting a legacy agent."""
    
    # Create enhanced agent with MCP support
    enhanced_agent = EnhancedAgent(
        agent_id="legacy_enhanced",
        capabilities=["legacy_task", "mcp_tools"],
        config={"timeout": 300}
    )
    
    # Create original legacy agent
    legacy_agent = LegacyAgent("legacy_original")
    
    # Register legacy methods as MCP tools
    tool_mapping = {
        "process_legacy_data": "legacy_method",
        "double_value": "another_legacy_method"
    }
    
    # Copy methods to enhanced agent
    enhanced_agent.legacy_method = legacy_agent.legacy_method
    enhanced_agent.another_legacy_method = legacy_agent.another_legacy_method
    
    # Register as MCP tools
    register_legacy_agent_tools(
        enhanced_agent,
        tool_mapping,
        category="legacy"
    )
    
    return enhanced_agent


async def main():
    """Example usage of MCP-compatible agents."""
    
    # Create MCP-compatible agent from decorator
    mcp_agent = ExampleAgent("mcp_example")
    
    # Create legacy agent conversion
    legacy_enhanced = convert_legacy_agent_example()
    
    # Test MCP tools
    print("Testing MCP tools:")
    
    # Test text processing tool
    result1 = await mcp_agent.execute_mcp_tool(
        "process_text",
        text="Hello World",
        operation="uppercase"
    )
    print(f"Text processing result: {result1}")
    
    # Test data analysis tool
    result2 = await mcp_agent.execute_mcp_tool(
        "analyze_data",
        data=[1, 2, 3, 4, 5]
    )
    print(f"Data analysis result: {result2}")
    
    # Test legacy tool
    result3 = await legacy_enhanced.execute_mcp_tool(
        "process_legacy_data",
        data="test data"
    )
    print(f"Legacy tool result: {result3}")
    
    # Display tool information
    print("\nRegistered MCP tools:")
    for tool_info in mcp_agent.get_mcp_tools_info():
        print(f"- {tool_info['name']}: {tool_info['description']}")
    
    for tool_info in legacy_enhanced.get_mcp_tools_info():
        print(f"- {tool_info['name']}: {tool_info['description']}")


if __name__ == "__main__":
    asyncio.run(main())
