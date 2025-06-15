"""Tool registration for MCP server."""

from .m365_tools import register_m365_tools
from .azure_tools import register_azure_tools
from .document_tools import register_document_tools
from .data_tools import register_data_tools
from .workflow_tools import register_workflow_tools

__all__ = [
    "register_all_tools",
    "register_m365_tools",
    "register_azure_tools", 
    "register_document_tools",
    "register_data_tools",
    "register_workflow_tools",
]


def register_all_tools(server, config):
    """Register all available tools with the MCP server."""
    
    # Register M365 tools
    register_m365_tools(server, config)
    
    # Register Azure tools (if configured)
    if config.azure.subscription_id:
        register_azure_tools(server, config)
        
    # Register document processing tools
    register_document_tools(server, config)
    
    # Register data analysis tools  
    register_data_tools(server, config)
    
    # Register workflow tools
    register_workflow_tools(server, config)
