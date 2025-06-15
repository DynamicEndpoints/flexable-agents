"""Tool registry for managing MCP tools."""

from typing import Dict, List, Callable, Any, Optional
import logging
from functools import wraps
import inspect
from .types import MCPTool, ToolParameter

logger = logging.getLogger(__name__)  # Reverted to standard logger


class ToolRegistry:
    """Registry for managing MCP tools."""
    
    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._handlers: Dict[str, Callable] = {}
        
    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable,
        parameters: Optional[List[ToolParameter]] = None,
        returns: Optional[str] = None,
        examples: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Register a new tool."""
        
        # Auto-generate parameters from function signature if not provided
        if parameters is None:
            parameters = self._extract_parameters(handler)
            
        tool = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            returns=returns,
            examples=examples
        )
        
        self._tools[name] = tool
        self._handlers[name] = handler
        logger.info(f"Registered tool: {name}")
        
    def unregister_tool(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
            del self._handlers[name]
            logger.info(f"Unregistered tool: {name}")
        else:
            logger.warning(f"Tool {name} not found for unregistration")
            
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return self._tools.get(name)
        
    def get_handler(self, name: str) -> Optional[Callable]:
        """Get a tool handler by name."""
        return self._handlers.get(name)
        
    def list_tools(self) -> List[MCPTool]:
        """List all registered tools."""
        return list(self._tools.values())
        
    def tool_exists(self, name: str) -> bool:
        """Check if a tool exists."""
        return name in self._tools
        
    def _extract_parameters(self, handler: Callable) -> List[ToolParameter]:
        """Extract parameters from function signature."""
        parameters = []
        sig = inspect.signature(handler)
        
        for param_name, param in sig.parameters.items():
            # Skip self parameter
            if param_name == 'self':
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
                    
            # Check if parameter is required
            required = param.default == inspect.Parameter.empty
            default = None if param.default == inspect.Parameter.empty else param.default
            
            # Extract description from docstring if available
            description = f"Parameter {param_name}"
            if handler.__doc__:
                # Simple extraction - could be improved with better parsing
                lines = handler.__doc__.split('\n')
                for line in lines:
                    if param_name in line and ':' in line:
                        description = line.split(':', 1)[1].strip()
                        break
                        
            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                description=description,
                required=required,
                default=default
            ))
            
        return parameters


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[List[ToolParameter]] = None,
    returns: Optional[str] = None,
    examples: Optional[List[Dict[str, Any]]] = None
):
    """Decorator for registering tools."""
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"
        
        # Store metadata on function for later registration
        func._mcp_tool_name = tool_name
        func._mcp_tool_description = tool_description
        func._mcp_tool_parameters = parameters
        func._mcp_tool_returns = returns
        func._mcp_tool_examples = examples
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def register_tools_from_module(registry: ToolRegistry, module: Any) -> None:
    """Register all tools from a module."""
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and hasattr(obj, '_mcp_tool_name'):
            registry.register_tool(
                name=obj._mcp_tool_name,
                description=obj._mcp_tool_description,
                handler=obj,
                parameters=obj._mcp_tool_parameters,
                returns=obj._mcp_tool_returns,
                examples=obj._mcp_tool_examples
            )
