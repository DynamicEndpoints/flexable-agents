#!/usr/bin/env python3
"""Main entry point for the Flexible Agents MCP Server."""

import asyncio
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp import MCPServer, ConfigManager
from src.mcp.config import create_sample_config
from src.tools import register_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)


def setup_logging(config: ConfigManager) -> None:
    """Setup logging configuration."""
    log_level = getattr(logging, config.server.log_level.upper())
    
    # Update root logger level
    logging.getLogger().setLevel(log_level)
    
    # Set specific logger levels
    if config.server.debug:
        logging.getLogger("src.mcp").setLevel(logging.DEBUG)
        logging.getLogger("src.tools").setLevel(logging.DEBUG)
    else:
        # Reduce noise from external libraries
        logging.getLogger("azure").setLevel(logging.WARNING)
        logging.getLogger("msal").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


async def main() -> None:
    """Main server function."""
    parser = argparse.ArgumentParser(description="Flexible Agents MCP Server")
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create sample configuration file and exit"
    )
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration and exit"
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List all available tools and exit"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit"
    )
    
    args = parser.parse_args()
    
    # Handle version
    if args.version:
        print("Flexible Agents MCP Server v2.0.0")
        return
        
    # Handle create config
    if args.create_config:
        create_sample_config()
        return
        
    # Load configuration
    try:
        config = ConfigManager(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
        
    # Override debug setting if specified
    if args.debug:
        config.server.debug = True
        config.server.log_level = "DEBUG"
        
    # Setup logging
    setup_logging(config)
    
    # Handle validate config
    if args.validate_config:
        issues = config.validate_config()
        if issues:
            print("Configuration issues found:")
            for section, problems in issues.items():
                print(f"  {section}:")
                for problem in problems:
                    print(f"    - {problem}")
            sys.exit(1)
        else:
            print("Configuration is valid!")
            return
            
    # Create and configure server
    server = MCPServer(
        name=config.server.name,
        version=config.server.version
    )
    
    # Register all tools
    try:
        register_all_tools(server, config)
        logger.info(f"Registered {len(server.tool_registry.list_tools())} tools")
    except Exception as e:
        logger.error(f"Failed to register tools: {e}")
        sys.exit(1)
        
    # Handle list tools
    if args.list_tools:
        tools = server.tool_registry.list_tools()
        print(f"Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        return
        
    # Validate configuration before starting
    config_issues = config.validate_config()
    if config_issues:
        logger.warning("Configuration issues detected:")
        for section, problems in config_issues.items():
            for problem in problems:
                logger.warning(f"  {section}: {problem}")
        logger.warning("Some tools may not work properly")
        
    # Start server
    logger.info(f"Starting {config.server.name} v{config.server.version}")
    logger.info(f"Debug mode: {config.server.debug}")
    logger.info(f"Log level: {config.server.log_level}")
    
    try:
        await server.run_stdio()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
