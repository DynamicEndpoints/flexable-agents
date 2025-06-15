"""MCP protocol types and data models."""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from enum import Enum
import uuid
from datetime import datetime


class MCPRequestType(str, Enum):
    """MCP request types."""
    INITIALIZE = "initialize"
    LIST_TOOLS = "tools/list"
    CALL_TOOL = "tools/call"
    GET_PROMPT = "prompts/get"
    LIST_PROMPTS = "prompts/list"
    LIST_RESOURCES = "resources/list"
    READ_RESOURCE = "resources/read"
    SUBSCRIBE = "resources/subscribe"
    UNSUBSCRIBE = "resources/unsubscribe"


class MCPResponseType(str, Enum):
    """MCP response types."""
    RESULT = "result"
    ERROR = "error"
    NOTIFICATION = "notification"


class MCPError(BaseModel):
    """MCP error response."""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class MCPRequest(BaseModel):
    """MCP request model."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = Field(default_factory=lambda: str(uuid.uuid4()))
    method: MCPRequestType
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP response model."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[MCPError] = None


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    returns: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to MCP protocol format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description,
                        **({"enum": param.enum} if param.enum else {}),
                        **({"default": param.default} if param.default is not None else {})
                    }
                    for param in self.parameters
                },
                "required": [param.name for param in self.parameters if param.required]
            }
        }


class MCPResource(BaseModel):
    """MCP resource definition."""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


class MCPPrompt(BaseModel):
    """MCP prompt definition."""
    name: str
    description: str
    arguments: Optional[List[ToolParameter]] = None


class ServerCapabilities(BaseModel):
    """Server capabilities declaration."""
    tools: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None


class ClientCapabilities(BaseModel):
    """Client capabilities declaration."""
    sampling: Optional[Dict[str, Any]] = None
    experimental: Optional[Dict[str, Any]] = None


class InitializeRequest(BaseModel):
    """Initialize request parameters."""
    protocolVersion: str
    capabilities: ClientCapabilities
    clientInfo: Dict[str, Any]


class InitializeResponse(BaseModel):
    """Initialize response."""
    protocolVersion: str = "2024-11-05"
    capabilities: ServerCapabilities
    serverInfo: Dict[str, Any]


class ToolCallRequest(BaseModel):
    """Tool call request parameters."""
    name: str
    arguments: Optional[Dict[str, Any]] = None


class ToolCallResponse(BaseModel):
    """Tool call response."""
    content: List[Dict[str, Any]]
    isError: bool = False
