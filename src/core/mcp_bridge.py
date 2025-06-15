"""Bridge module for converting existing agents to MCP-compatible agents."""

import logging
import inspect
from typing import Dict, Any, List, Optional, Callable, Type, Union
from functools import wraps

from .base import Agent, Task, TaskResult
from .base_mcp import EnhancedAgent, MCPToolMetadata, mcp_tool, create_mcp_tool_metadata

logger = logging.getLogger(__name__)


class AgentMCPBridge:
    """Bridge to convert existing agents to MCP-compatible agents."""
    
    @staticmethod
    def convert_agent_to_mcp(
        agent_class: Type[Agent],
        mcp_tools: Optional[List[MCPToolMetadata]] = None,
        auto_discover_tools: bool = True
    ) -> Type[EnhancedAgent]:
        """Convert an existing agent class to MCP-compatible agent."""
        
        class MCPCompatibleAgent(EnhancedAgent):
            """MCP-compatible wrapper for existing agent."""
            
            def __init__(self, *args, **kwargs):
                # Extract MCP-specific arguments
                config = kwargs.pop('config', {})
                tools = kwargs.pop('mcp_tools', mcp_tools or [])
                
                # Initialize the enhanced agent
                super().__init__(
                    agent_id=kwargs.get('agent_id', 'agent'),
                    capabilities=kwargs.get('capabilities', []),
                    config=config,
                    mcp_tools=tools
                )
                
                # Initialize the original agent
                self._original_agent = agent_class(*args, **kwargs)
                
                # Copy attributes from original agent
                for attr_name in dir(self._original_agent):
                    if not attr_name.startswith('_') and not hasattr(self, attr_name):
                        attr_value = getattr(self._original_agent, attr_name)
                        setattr(self, attr_name, attr_value)
                
                # Auto-discover MCP tools if requested
                if auto_discover_tools:
                    self._auto_discover_mcp_tools()
            
            async def process_task(self, task: Task) -> TaskResult:
                """Process task using original agent implementation."""
                return await self._original_agent.process_task(task)
            
            async def handle_message(self, message):
                """Handle message using original agent implementation."""
                return await self._original_agent.handle_message(message)
            
            def _auto_discover_mcp_tools(self):
                """Auto-discover MCP tools from agent methods."""
                for method_name in dir(self._original_agent):
                    method = getattr(self._original_agent, method_name)
                    
                    if (callable(method) and 
                        not method_name.startswith('_') and
                        hasattr(method, '_mcp_tool_name')):
                        
                        # Create tool metadata from decorated method
                        metadata = create_mcp_tool_metadata(
                            name=method._mcp_tool_name,
                            description=method._mcp_tool_description,
                            parameters=AgentMCPBridge._extract_parameters_schema(method),
                            category=getattr(method, '_mcp_tool_category', None),
                            tags=getattr(method, '_mcp_tool_tags', []),
                            examples=getattr(method, '_mcp_tool_examples', [])
                        )
                        
                        self.register_mcp_tool(metadata, method)
                        logger.info(f"Auto-discovered MCP tool: {method._mcp_tool_name}")
        
        # Copy class metadata
        MCPCompatibleAgent.__name__ = f"MCP{agent_class.__name__}"
        MCPCompatibleAgent.__doc__ = f"MCP-compatible version of {agent_class.__name__}"
        
        return MCPCompatibleAgent
    
    @staticmethod
    def _extract_parameters_schema(method: Callable) -> Dict[str, Any]:
        """Extract parameter schema from method signature."""
        sig = inspect.signature(method)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'cls']:
                continue
                
            # Determine parameter type
            param_type = "string"  # default
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"
                elif hasattr(param.annotation, '__origin__'):
                    # Handle generic types like Optional[str], List[int], etc.
                    origin = param.annotation.__origin__
                    if origin is list:
                        param_type = "array"
                    elif origin is dict:
                        param_type = "object"
                    elif origin is Union:
                        # For Optional types, check if None is in the union
                        args = param.annotation.__args__
                        if type(None) in args:
                            # It's Optional, use the non-None type
                            non_none_types = [arg for arg in args if arg != type(None)]
                            if non_none_types:
                                first_type = non_none_types[0]
                                if first_type == str:
                                    param_type = "string"
                                elif first_type == int:
                                    param_type = "integer"
                                elif first_type == float:
                                    param_type = "number"
                                elif first_type == bool:
                                    param_type = "boolean"
                                elif first_type == list:
                                    param_type = "array"
                                elif first_type == dict:
                                    param_type = "object"
            
            # Create property definition
            prop_def = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }
            
            # Add default value if present
            if param.default != inspect.Parameter.empty:
                if param.default is not None:
                    prop_def["default"] = param.default
            else:
                # Parameter is required if no default
                required.append(param_name)
            
            properties[param_name] = prop_def
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    @staticmethod
    def create_mcp_wrapper_function(
        original_func: Callable,
        tool_name: str,
        description: str = None,
        category: str = None,
        tags: List[str] = None,
        examples: List[Dict[str, Any]] = None
    ) -> Callable:
        """Create an MCP-compatible wrapper for an existing function."""
        
        @mcp_tool(
            name=tool_name,
            description=description or original_func.__doc__ or f"Tool: {tool_name}",
            category=category,
            tags=tags,
            examples=examples
        )
        @wraps(original_func)
        async def mcp_wrapper(*args, **kwargs):
            """MCP wrapper function."""
            if inspect.iscoroutinefunction(original_func):
                return await original_func(*args, **kwargs)
            else:
                return original_func(*args, **kwargs)
        
        return mcp_wrapper


def mcp_compatible_agent(
    mcp_tools: Optional[List[MCPToolMetadata]] = None,
    auto_discover: bool = True,
    config: Optional[Dict[str, Any]] = None
):
    """Class decorator to make an agent MCP-compatible."""
    
    def decorator(agent_class: Type[Agent]) -> Type[EnhancedAgent]:
        return AgentMCPBridge.convert_agent_to_mcp(
            agent_class=agent_class,
            mcp_tools=mcp_tools,
            auto_discover_tools=auto_discover
        )
    
    return decorator


def register_legacy_agent_tools(
    agent: EnhancedAgent,
    tool_mapping: Dict[str, str],
    category: str = None
):
    """Register legacy agent methods as MCP tools."""
    
    for tool_name, method_name in tool_mapping.items():
        if hasattr(agent, method_name):
            method = getattr(agent, method_name)
            
            # Create metadata
            metadata = create_mcp_tool_metadata(
                name=tool_name,
                description=f"Legacy method: {method_name}",
                parameters=AgentMCPBridge._extract_parameters_schema(method),
                category=category
            )
            
            # Register the tool
            agent.register_mcp_tool(metadata, method)
            logger.info(f"Registered legacy method {method_name} as MCP tool {tool_name}")


# Utility functions for common agent patterns
def create_standard_m365_tools(agent_prefix: str = "") -> List[MCPToolMetadata]:
    """Create standard M365 tool metadata."""
    prefix = f"{agent_prefix}_" if agent_prefix else ""
    
    return [
        create_mcp_tool_metadata(
            name=f"{prefix}user_management",
            description="Manage Microsoft 365 users",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "update", "delete", "get", "list", "enable", "disable"],
                        "description": "Action to perform"
                    },
                    "user_data": {
                        "type": "object",
                        "description": "User data for create/update operations"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User ID for operations"
                    }
                },
                "required": ["action"]
            },
            category="m365",
            tags=["users", "administration"]
        ),
        create_mcp_tool_metadata(
            name=f"{prefix}group_management",
            description="Manage Microsoft 365 groups",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "update", "delete", "get", "list", "add_member", "remove_member"],
                        "description": "Action to perform"
                    },
                    "group_data": {
                        "type": "object",
                        "description": "Group data for create/update operations"
                    },
                    "group_id": {
                        "type": "string",
                        "description": "Group ID for operations"
                    }
                },
                "required": ["action"]
            },
            category="m365",
            tags=["groups", "administration"]
        )
    ]
