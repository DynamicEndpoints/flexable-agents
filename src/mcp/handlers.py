"""Tool execution handlers for MCP server."""

from typing import Dict, Any, Optional, List
import logging
import traceback
import asyncio
import time
from datetime import datetime
import json  # Added import
from .types import ToolCallRequest, ToolCallResponse, MCPError
from .registry import ToolRegistry
from .logging_system import log_request_metrics, get_logger_manager

logger = logging.getLogger(__name__)


class ToolHandler:
    """Handles tool execution for MCP server."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.execution_history: List[Dict[str, Any]] = []
        
    async def execute_tool(self, request: ToolCallRequest) -> ToolCallResponse:
        """Execute a tool call request with enhanced logging."""
        start_time = time.time()
        # success variable for the finally block of this function,
        # indicating if execute_tool itself completed without an unhandled exception.
        execute_tool_success_flag = True
        execute_tool_error_message = None
        
        args = request.arguments or {} # Define args early for use in _record_execution if validation fails

        try:
            # Get the tool handler
            handler = self.registry.get_handler(request.name)
            if not handler:
                error_message = f"Tool '{request.name}' not found"
                # This case will be caught by the generic Exception handler below
                raise ValueError(error_message)
                
            # Validate tool exists
            tool = self.registry.get_tool(request.name)
            if not tool:
                error_message = f"Tool definition for '{request.name}' not found"
                raise ValueError(error_message)
                
            # Prepare arguments (already done)
            # args = request.arguments or {} 
            
            # Validate required parameters
            self._validate_parameters(tool, args) # This can raise ValueError
            
            # Execute the tool
            logger.info(f"Executing tool: {request.name} with args: {args}")
            
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**args)
            else:
                result = handler(**args)
                
            # Determine actual tool success based on the result
            tool_actually_succeeded = True
            error_from_tool_str = None
            if isinstance(result, dict) and result.get("status") == "error":
                tool_actually_succeeded = False
                error_from_tool_str = result.get("message") or json.dumps(result)

            content = self._format_response_content(result)
            
            execution_time = time.time() - start_time
            self._record_execution(request.name, args, tool_actually_succeeded, execution_time, error_from_tool_str)
            
            return ToolCallResponse(
                content=content,
                isError=not tool_actually_succeeded
            )
            
        except Exception as e:
            execute_tool_success_flag = False
            execute_tool_error_message = str(e)
            logger.error(f"Error executing tool {request.name}: {execute_tool_error_message}")
            logger.debug(traceback.format_exc())
            
            execution_time = time.time() - start_time # Recalculate time up to the error
            # Record failed execution (tool crashed or validation failed)
            # args might not be fully prepared if error is in validation, so use request.arguments
            self._record_execution(request.name, request.arguments or {}, False, execution_time, execute_tool_error_message)
            
            error_content_dict = {
                "status": "error",
                "error_code": "TOOL_EXECUTION_FAILURE",
                "message": f"An unexpected error occurred while executing tool '{request.name}'.",
                "details": execute_tool_error_message,
                "resolution": "Check server logs for more details or contact support."
            }
            
            return ToolCallResponse(
                content=[{
                    "type": "application/json",
                    "json": error_content_dict
                }],
                isError=True
            )
        finally:
            # The log_request_metrics for tool_execution is now handled by _record_execution.
            # No further logging here for f"tool_execution:{request.name}"
            pass
            
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
            # Check if it's a structured error response from our tools
            if result.get("status") == "error" and "error_code" in result:
                return [{
                    "type": "application/json", 
                    "json": result 
                }]
            # For other dictionaries, format as a JSON string in a text content part
            else: # "status" removed from any() to avoid conflict, and any() is broad.
                  # Defaulting to json.dumps for all other dicts for structured output.
                try:
                    return [{"type": "text", "text": json.dumps(result, indent=2)}]
                except TypeError: # Handle non-serializable dicts
                    return [{"type": "text", "text": str(result)}]

        if isinstance(result, list):
            # Try to dump list as JSON array string if possible
            try:
                return [{"type": "text", "text": json.dumps(result, indent=2)}]
            except TypeError: # Handle non-serializable items in list
                 return [{"type": "text", "text": "\\n".join(str(item) for item in result)}]
            
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
        """Record tool execution history with enhanced logging."""
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
            
        # Log to enhanced logging system
        log_request_metrics(f"tool_execution:{tool_name}", execution_time, success, error)
            
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
            "recent_executions": [
                {
                    "timestamp": exec["timestamp"].isoformat(),
                    "tool_name": exec["tool_name"],
                    "success": exec["success"],
                    "execution_time": exec["execution_time"],
                    "error": exec.get("error")
                }
                for exec in self.execution_history[-10:]  # Last 10 executions
            ]
        }
