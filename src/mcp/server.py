"""MCP Server implementation."""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

from .types import (
    MCPRequest, MCPResponse, MCPError, MCPRequestType,
    InitializeRequest, InitializeResponse, ServerCapabilities,
    ToolCallRequest, ToolCallResponse
)
from .registry import ToolRegistry
from .handlers import ToolHandler
from .logging_system import log_request_metrics, get_logger_manager

logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol server implementation."""
    
    def __init__(self, name: str = "Flexible Agents MCP Server", version: str = "2.0.0"):
        self.name = name
        self.version = version
        self.initialized = False
        self.client_capabilities = None
        
        # Core components
        self.tool_registry = ToolRegistry()
        self.tool_handler = ToolHandler(self.tool_registry)
        
        # Server state
        self.start_time = datetime.now()
        self.request_count = 0
        
        logger.info(f"Initialized MCP Server: {name} v{version}")
        
    async def handle_request(self, request_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Handle incoming MCP request with enhanced logging."""
        start_time = time.time()
        success = True
        error_message = None
        method = "unknown"
        
        try:
            # Parse request if it's a string
            if isinstance(request_data, str):
                request_data = json.loads(request_data)
                
            # Validate and parse request
            request = MCPRequest(**request_data)
            method = request.method
            self.request_count += 1
            
            logger.debug(f"Handling request: {request.method} (ID: {request.id})")
            
            # Route request to appropriate handler
            if request.method == MCPRequestType.INITIALIZE:
                response_data = await self._handle_initialize(request)
            elif request.method == MCPRequestType.LIST_TOOLS:
                response_data = await self._handle_list_tools(request)
            elif request.method == MCPRequestType.CALL_TOOL:
                response_data = await self._handle_call_tool(request)
            else:
                error_message = f"Unknown method: {request.method}"
                success = False
                response_data = MCPResponse(
                    id=request.id,
                    error=MCPError(code=-1, message=error_message)
                ).dict()
                
            return response_data
            
        except json.JSONDecodeError as e:
            error_message = f"Invalid JSON: {str(e)}"
            success = False
            logger.error(error_message)
            return MCPResponse(
                id="",
                error=MCPError(code=-2, message=error_message)
            ).dict()
            
        except Exception as e:
            error_message = f"Request handling error: {str(e)}"
            success = False
            logger.error(error_message, exc_info=True)
            return MCPResponse(
                id=getattr(request, 'id', ""),
                error=MCPError(code=-3, message=error_message)
            ).dict()
        finally:
            # Log request metrics
            execution_time = time.time() - start_time
            log_request_metrics(f"mcp_request:{method}", execution_time, success, error_message)
            
    async def _handle_initialize(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle initialize request."""
        if not request.params:
            return MCPResponse(
                id=request.id,
                error=MCPError(code=-1, message="Missing initialize parameters")
            ).dict()
            
        try:
            init_request = InitializeRequest(**request.params)
            self.client_capabilities = init_request.capabilities
            self.initialized = True
            
            # Build server capabilities
            capabilities = ServerCapabilities(
                tools={
                    "listChanged": False
                }
            )
            
            response = InitializeResponse(
                protocolVersion="1.0.0",
                capabilities=capabilities,
                serverInfo={
                    "name": self.name,
                    "version": self.version
                }
            )
            
            return MCPResponse(id=request.id, result=response.dict()).dict()
            
        except Exception as e:
            logger.error(f"Error handling initialize: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(code=-2, message=f"Initialize failed: {str(e)}")
            ).dict()
            
    async def _handle_list_tools(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle list tools request."""
        try:
            tools = self.tool_registry.list_tools()
            tools_dict = [tool.dict() for tool in tools]
            
            return MCPResponse(
                id=request.id,
                result={"tools": tools_dict}
            ).dict()
            
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(code=-1, message=f"Failed to list tools: {str(e)}")
            ).dict()
            
    async def _handle_call_tool(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tool call request."""
        try:
            if not request.params:
                return MCPResponse(
                    id=request.id,
                    error=MCPError(code=-1, message="Missing tool call parameters")
                ).dict()
                
            tool_request = ToolCallRequest(**request.params)
            response = await self.tool_handler.execute_tool(tool_request)
            
            if response.isError:
                return MCPResponse(
                    id=request.id,
                    error=MCPError(code=-2, message="Tool execution failed"),
                    result={"content": response.content}
                ).dict()
            else:
                return MCPResponse(
                    id=request.id,
                    result={"content": response.content}
                ).dict()
                
        except Exception as e:
            logger.error(f"Error calling tool: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(code=-3, message=f"Tool call failed: {str(e)}")
            ).dict()
            
    def register_tool(
        self,
        name: str,
        description: str,
        handler,
        parameters: Optional[List] = None,
        returns: Optional[str] = None,
        examples: Optional[List] = None
    ) -> None:
        """Register a tool with the server."""
        self.tool_registry.register_tool(name, description, handler, parameters, returns, examples)
        
    def get_available_tools(self) -> List:
        """Get list of available tools."""
        return self.tool_registry.list_tools()
        
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Get tool execution stats
        tool_stats = self.tool_handler.get_execution_stats()
        
        # Get health status from logger manager
        logger_manager = get_logger_manager()
        health_status = logger_manager.get_health_status() if logger_manager else {"status": "unknown"}
        
        return {
            "server_info": {
                "name": self.name,
                "version": self.version,
                "start_time": self.start_time.isoformat(),
                "uptime_seconds": uptime,
                "initialized": self.initialized
            },
            "request_stats": {
                "total_requests": self.request_count,
                "requests_per_minute": (self.request_count / uptime) * 60 if uptime > 0 else 0
            },
            "tool_stats": tool_stats,
            "health": health_status
        }
        
    async def run_stdio(self):
        """Run server using stdio transport."""
        logger.info("Starting MCP server with stdio transport")
        
        try:
            # Read from stdin and write to stdout
            while True:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                # Process the request
                response = await self.handle_request(line)
                
                # Write response to stdout
                print(json.dumps(response))
                sys.stdout.flush()
                
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            
    async def shutdown(self):
        """Gracefully shutdown the server."""
        logger.info("Shutting down MCP server")
        # Any cleanup logic here
        logger.info("MCP server shutdown complete")
