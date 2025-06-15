"""Command line interface for Flexible Agents."""

import click
import json
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp import ConfigManager
from src.mcp.config import create_sample_config
from src.mcp.logging_system import setup_logging  # Import setup_logging

# Initialize logging with default settings for CLI operations
# This ensures that modules like ConfigManager use the enhanced logging
# system even when invoked via CLI commands that don't start the full server.
# The main server.py will call setup_enhanced_logging again with specific config.
setup_logging()


@click.group()
@click.version_option(version="2.0.0", prog_name="Flexible Agents")
def cli():
    """Flexible Agents MCP Server CLI."""
    pass


@cli.command()
@click.option("--config", default="config.json", help="Configuration file path")
def validate_config(config: str):
    """Validate configuration file."""
    try:
        config_manager = ConfigManager(config)
        issues = config_manager.validate_config()
        
        if issues:
            click.echo("Configuration issues found:", err=True)
            for section, problems in issues.items():
                click.echo(f"  {section}:", err=True)
                for problem in problems:
                    click.echo(f"    - {problem}", err=True)
            sys.exit(1)
        else:
            click.echo("Configuration is valid!", fg="green")
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
def create_config():
    """Create sample configuration files."""
    create_sample_config()
    click.echo("Sample configuration files created:", fg="green")
    click.echo("  - config.json.example")
    click.echo("  - .env.example")
    click.echo("Copy these files and update with your actual values.")


@cli.command()
@click.option("--config", default="config.json", help="Configuration file path")
def show_config(config: str):
    """Show current configuration."""
    try:
        config_manager = ConfigManager(config)
        config_data = config_manager.get_all_config()
        
        # Mask sensitive values
        if "client_secret" in str(config_data):
            config_data["m365"]["client_secret"] = "***masked***"
        if "api_key" in str(config_data):
            config_data["anthropic"]["api_key"] = "***masked***"
            
        click.echo(json.dumps(config_data, indent=2))
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.json", help="Configuration file path")
def list_tools(config: str):
    """List all available tools."""
    try:
        from src.mcp import MCPServer
        from src.tools import register_all_tools
        
        config_manager = ConfigManager(config)
        server = MCPServer()
        register_all_tools(server, config_manager)
        
        tools = server.tool_registry.list_tools()
        click.echo(f"Available tools ({len(tools)}):")
        for tool in tools:
            click.echo(f"  - {tool.name}: {tool.description}")
    except Exception as e:
        click.echo(f"Error listing tools: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.json", help="Configuration file path")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def server(config: str, debug: bool):
    """Start the MCP server."""
    import subprocess
    import sys
    
    args = [sys.executable, "server.py", "--config", config]
    if debug:
        args.append("--debug")
        
    try:
        subprocess.run(args)
    except KeyboardInterrupt:
        click.echo("Server stopped by user")


@cli.command()
@click.argument("tool_name")
@click.argument("parameters", required=False)
@click.option("--config", default="config.json", help="Configuration file path")
def test_tool(tool_name: str, parameters: Optional[str], config: str):
    """Test a specific tool."""
    async def _test_tool():
        try:
            from src.mcp import MCPServer
            from src.tools import register_all_tools
            from src.mcp.types import ToolCallRequest
            
            config_manager = ConfigManager(config)
            server = MCPServer()
            register_all_tools(server, config_manager)
            
            # Parse parameters
            params = {}
            if parameters:
                try:
                    params = json.loads(parameters)
                except json.JSONDecodeError:
                    click.echo("Invalid JSON parameters", err=True)
                    return
                    
            # Create tool request
            request = ToolCallRequest(name=tool_name, arguments=params)
            
            # Execute tool
            response = await server.tool_handler.execute_tool(request)
            
            if response.isError:
                click.echo("Tool execution failed:", err=True)
                for content in response.content:
                    click.echo(content.get("text", ""), err=True)
            else:
                click.echo("Tool execution successful:")
                for content in response.content:
                    click.echo(content.get("text", ""))
                    
        except Exception as e:
            click.echo(f"Error testing tool: {e}", err=True)
            
    asyncio.run(_test_tool())


if __name__ == "__main__":
    cli()
