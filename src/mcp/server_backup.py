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
                raise ValueError(f"Unsupported method: {request.method}")
                
            # Create response
            response = MCPResponse(
                id=request.id,
                result=response_data
            )
            
            return response.dict(exclude_none=True)
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            
            # Extract request ID if possible
            request_id = None
            if isinstance(request_data, dict):
                request_id = request_data.get("id")
            elif hasattr(request_data, "id"):
                request_id = request_data.id
                
            # Create error response
            error_response = MCPResponse(
                id=request_id,
                error=MCPError(
                    code=-32603,  # Internal error
                    message=str(e)
                )
            )
            
            return error_response.dict(exclude_none=True)
            
    async def _handle_initialize(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle initialize request."""
        if not request.params:
            raise ValueError("Initialize request missing parameters")
            
        init_request = InitializeRequest(**request.params)
        self.client_capabilities = init_request.capabilities
        
        # Create server capabilities
        server_capabilities = ServerCapabilities(
            tools={
                "listChanged": False  # We don't support dynamic tool changes yet
            },
            prompts={
                "listChanged": False
            },
            resources={
                "subscribe": False,
                "listChanged": False
            }
        )
        
        # Create response
        response = InitializeResponse(
            capabilities=server_capabilities,
            serverInfo={
                "name": self.name,
                "version": self.version,
                "description": "Flexible Agents MCP Server for Microsoft 365 Administration",
                "author": "Flexible Agents Team",
                "homepage": "https://github.com/flexible-agents/flexible-agents-mcp"
            }
        )
        
        self.initialized = True
        logger.info("Server initialized successfully")
        
        return response.dict()
        
    async def _handle_list_tools(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle list tools request."""
        if not self.initialized:
            raise ValueError("Server not initialized")
            
        tools = self.tool_registry.list_tools()
        
        return {
            "tools": [tool.to_dict() for tool in tools]
        }
        
    async def _handle_call_tool(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle call tool request."""
        if not self.initialized:
            raise ValueError("Server not initialized")
            
        if not request.params:
            raise ValueError("Tool call request missing parameters")
            
        tool_request = ToolCallRequest(**request.params)
        response = await self.tool_handler.execute_tool(tool_request)
        
        return response.dict()
        
    def register_tool(self, *args, **kwargs) -> None:
        """Register a tool with the server."""
        self.tool_registry.register_tool(*args, **kwargs)
        
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and statistics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "name": self.name,
            "version": self.version,
            "initialized": self.initialized,
            "uptime_seconds": uptime,
            "request_count": self.request_count,
            "tool_count": len(self.tool_registry.list_tools()),
            "execution_stats": self.tool_handler.get_execution_stats(),
            "start_time": self.start_time.isoformat(),
            "client_capabilities": self.client_capabilities.dict() if self.client_capabilities else None
        }
        
    async def run_stdio(self) -> None:
        """Run server using stdio transport."""
        logger.info("Starting MCP server with stdio transport")
        
        try:
            while True:
                # Read request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                # Process request
                response = await self.handle_request(line)
                
                # Send response to stdout
                print(json.dumps(response), flush=True)
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            raise
            
    async def shutdown(self) -> None:
        """Shutdown the server gracefully."""
        logger.info("Shutting down MCP server")
        self.initialized = False
