"""Tool execution handlers for MCP server."""

from typing import Dict, Any, Optional, List
import logging
import traceback
import asyncio
from datetime import datetime
from .types import ToolCallRequest, ToolCallResponse, MCPError
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolHandler:
    """Handles tool execution for MCP server."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.execution_history: List[Dict[str, Any]] = []
        
    async def execute_tool(self, request: ToolCallRequest) -> ToolCallResponse:
        """Execute a tool call request."""
        start_time = datetime.now()
        
        try:
            # Get the tool handler
            handler = self.registry.get_handler(request.name)
            if not handler:
                raise ValueError(f"Tool '{request.name}' not found")
                
            # Validate tool exists
            tool = self.registry.get_tool(request.name)
            if not tool:
                raise ValueError(f"Tool definition for '{request.name}' not found")
                
            # Prepare arguments
            args = request.arguments or {}
            
            # Validate required parameters
            self._validate_parameters(tool, args)
            
            # Execute the tool
            logger.info(f"Executing tool: {request.name} with args: {args}")
            
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**args)
            else:
                result = handler(**args)
                
            # Format response
            content = self._format_response_content(result)
            
            # Record execution
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_execution(request.name, args, True, execution_time)
            
            return ToolCallResponse(
                content=content,
                isError=False
            )
            
        except Exception as e:
            logger.error(f"Error executing tool {request.name}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # Record failed execution
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_execution(request.name, request.arguments or {}, False, execution_time, str(e))
            
            return ToolCallResponse(
                content=[{
                    "type": "text",
                    "text": f"Error executing tool {request.name}: {str(e)}"
                }],
                isError=True
            )
            
    def _validate_parameters(self, tool, args: Dict[str, Any]) -> None:
        """Validate tool parameters."""
        required_params = [p.name for p in tool.parameters if p.required]
        
        # Check required parameters
        missing_params = [p for p in required_params if p not in args]
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
            
        # Validate parameter types (basic validation)
        for param in tool.parameters:
            if param.name in args:
                value = args[param.name]
                if not self._validate_parameter_type(value, param.type):
                    raise ValueError(f"Parameter '{param.name}' should be of type {param.type}")
                    
    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type."""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        return True  # Unknown type, allow it
        
    def _format_response_content(self, result: Any) -> List[Dict[str, Any]]:
        """Format tool execution result into MCP response content."""
        if result is None:
            return [{
                "type": "text",
                "text": "Tool executed successfully (no output)"
            }]
            
        if isinstance(result, str):
            return [{
                "type": "text",
                "text": result
            }]
            
        if isinstance(result, dict):
            # If it looks like structured data, format as JSON
            if any(key in result for key in ["status", "data", "result", "output"]):
                return [{
                    "type": "text",
                    "text": str(result)
                }]
            else:
                # Format as readable text
                formatted = []
                for key, value in result.items():
                    formatted.append(f"{key}: {value}")
                return [{
                    "type": "text",
                    "text": "\n".join(formatted)
                }]
                
        if isinstance(result, list):
            return [{
                "type": "text",
                "text": "\n".join(str(item) for item in result)
            }]
            
        # Default: convert to string
        return [{
            "type": "text", 
            "text": str(result)
        }]
        
    def _record_execution(
        self,
        tool_name: str,
        args: Dict[str, Any],
        success: bool,
        execution_time: float,
        error: Optional[str] = None
    ) -> None:
        """Record tool execution history."""
        self.execution_history.append({
            "timestamp": datetime.now(),
            "tool_name": tool_name,
            "arguments": args,
            "success": success,
            "execution_time": execution_time,
            "error": error
        })
        
        # Keep only last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
            
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {"total_executions": 0}
            
        total = len(self.execution_history)
        successful = sum(1 for exec in self.execution_history if exec["success"])
        failed = total - successful
        
        avg_execution_time = sum(exec["execution_time"] for exec in self.execution_history) / total
        
        # Tool usage stats
        tool_usage = {}
        for exec in self.execution_history:
            tool_name = exec["tool_name"]
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
            
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": successful / total if total > 0 else 0,
            "average_execution_time": avg_execution_time,
            "tool_usage": tool_usage,
            "recent_executions": self.execution_history[-10:]  # Last 10 executions
        }
