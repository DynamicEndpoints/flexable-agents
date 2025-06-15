"""Configuration management for MCP server."""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Server configuration."""
    name: str = "Flexible Agents MCP Server"
    version: str = "2.0.0"
    debug: bool = False
    log_level: str = "INFO"
    max_execution_history: int = 1000
    timeout_seconds: int = 300
    
    
@dataclass
class M365Config:
    """Microsoft 365 configuration."""
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authority: Optional[str] = None
    scopes: list = None
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = [
                "https://graph.microsoft.com/.default"
            ]
            

@dataclass
class AnthropicConfig:
    """Anthropic configuration."""
    api_key: Optional[str] = None
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.0
    

@dataclass
class AzureConfig:
    """Azure configuration."""
    subscription_id: Optional[str] = None
    resource_group: Optional[str] = None
    location: str = "eastus"
    

class ConfigManager:
    """Configuration manager for MCP server."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("config.json")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize configurations
        self.server = ServerConfig()
        self.m365 = M365Config()
        self.anthropic = AnthropicConfig()
        self.azure = AzureConfig()
        
        # Load configuration
        self._load_config()
        self._load_env_overrides()
        
    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    
                # Update configurations
                if 'server' in config_data:
                    self._update_dataclass(self.server, config_data['server'])
                if 'm365' in config_data:
                    self._update_dataclass(self.m365, config_data['m365'])
                if 'anthropic' in config_data:
                    self._update_dataclass(self.anthropic, config_data['anthropic'])
                if 'azure' in config_data:
                    self._update_dataclass(self.azure, config_data['azure'])
                    
                logger.info(f"Loaded configuration from {self.config_path}")
                
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_path}: {e}")
        else:
            logger.info(f"Config file {self.config_path} not found, using defaults")
            
    def _load_env_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        
        # Server config
        if os.getenv("MCP_DEBUG"):
            self.server.debug = os.getenv("MCP_DEBUG").lower() == "true"
        if os.getenv("MCP_LOG_LEVEL"):
            self.server.log_level = os.getenv("MCP_LOG_LEVEL")
            
        # M365 config
        if os.getenv("AZURE_TENANT_ID"):
            self.m365.tenant_id = os.getenv("AZURE_TENANT_ID")
        if os.getenv("AZURE_CLIENT_ID"):
            self.m365.client_id = os.getenv("AZURE_CLIENT_ID")
        if os.getenv("AZURE_CLIENT_SECRET"):
            self.m365.client_secret = os.getenv("AZURE_CLIENT_SECRET")
            
        # Anthropic config
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic.api_key = os.getenv("ANTHROPIC_API_KEY")
        if os.getenv("ANTHROPIC_MODEL"):
            self.anthropic.model = os.getenv("ANTHROPIC_MODEL")
            
        # Azure config
        if os.getenv("AZURE_SUBSCRIPTION_ID"):
            self.azure.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        if os.getenv("AZURE_RESOURCE_GROUP"):
            self.azure.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
            
    def _update_dataclass(self, obj: Any, data: Dict[str, Any]) -> None:
        """Update dataclass with dictionary data."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
                
    def save_config(self, config_path: Optional[str] = None) -> None:
        """Save current configuration to file."""
        path = Path(config_path) if config_path else self.config_path
        
        config_data = {
            'server': asdict(self.server),
            'm365': asdict(self.m365),
            'anthropic': asdict(self.anthropic),
            'azure': asdict(self.azure)
        }
        
        try:
            with open(path, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Saved configuration to {path}")
        except Exception as e:
            logger.error(f"Failed to save config to {path}: {e}")
            
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return {
            'server': asdict(self.server),
            'm365': asdict(self.m365),
            'anthropic': asdict(self.anthropic),
            'azure': asdict(self.azure)
        }
        
    def validate_config(self) -> Dict[str, List[str]]:
        """Validate configuration and return any issues."""
        issues = {
            'm365': [],
            'anthropic': [],
            'azure': []
        }
        
        # Validate M365 config
        if not self.m365.tenant_id:
            issues['m365'].append("Missing tenant_id")
        if not self.m365.client_id:
            issues['m365'].append("Missing client_id")
        if not self.m365.client_secret:
            issues['m365'].append("Missing client_secret")
            
        # Validate Anthropic config
        if not self.anthropic.api_key:
            issues['anthropic'].append("Missing api_key")
            
        # Validate Azure config (optional, only if using Azure tools)
        # These are only warnings since Azure tools are optional
        
        # Remove empty issue lists
        return {k: v for k, v in issues.items() if v}


def create_sample_config() -> None:
    """Create a sample configuration file."""
    config = {
        "server": {
            "name": "Flexible Agents MCP Server",
            "version": "2.0.0",
            "debug": False,
            "log_level": "INFO",
            "max_execution_history": 1000,
            "timeout_seconds": 300
        },
        "m365": {
            "tenant_id": "your-tenant-id",
            "client_id": "your-client-id", 
            "client_secret": "your-client-secret",
            "authority": "https://login.microsoftonline.com/your-tenant-id",
            "scopes": ["https://graph.microsoft.com/.default"]
        },
        "anthropic": {
            "api_key": "your-anthropic-api-key",
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4096,
            "temperature": 0.0
        },
        "azure": {
            "subscription_id": "your-azure-subscription-id",
            "resource_group": "your-resource-group",
            "location": "eastus"
        }
    }
    
    config_path = Path("config.json.example")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        
    print(f"Sample configuration created at {config_path}")
    print("Copy this to config.json and update with your actual values.")
