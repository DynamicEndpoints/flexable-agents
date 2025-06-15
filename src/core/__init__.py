"""Core classes for the Flexible Agents system with MCP compatibility."""

from .base import (
    Message, Task, TaskResult, Agent, AgentSystem,
    EnhancedAgent, EnhancedAgentSystem, MCPToolMetadata,
    AgentError, TaskExecutionError, create_mcp_tool_metadata, mcp_tool
)

from .mcp_bridge import (
    AgentMCPBridge, mcp_compatible_agent, register_legacy_agent_tools,
    create_standard_m365_tools
)

# For backward compatibility
from .base_mcp import (
    Agent as MCPAgent,
    AgentSystem as MCPAgentSystem
)

__all__ = [
    # Base classes
    "Message", "Task", "TaskResult", "Agent", "AgentSystem",
    
    # Enhanced MCP classes
    "EnhancedAgent", "EnhancedAgentSystem", "MCPAgent", "MCPAgentSystem",
    
    # MCP metadata and decorators
    "MCPToolMetadata", "create_mcp_tool_metadata", "mcp_tool",
    
    # Exceptions
    "AgentError", "TaskExecutionError",
    
    # Bridge utilities
    "AgentMCPBridge", "mcp_compatible_agent", "register_legacy_agent_tools",
    "create_standard_m365_tools"
]