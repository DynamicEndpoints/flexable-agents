# Flexible Agents MCP Server - Windows PowerShell Script
# This script helps you run the MCP server on Windows

param(
    [string]$Config = "config.json",
    [switch]$Debug,
    [switch]$CreateConfig,
    [switch]$ValidateConfig,
    [switch]$ListTools,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.9 or later."
    exit 1
}

# Check if virtual environment exists
$venvPath = Join-Path $ScriptDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & $activateScript
} else {
    Write-Error "Failed to create virtual environment"
    exit 1
}

# Install dependencies
$requirementsPath = Join-Path $ScriptDir "requirements.txt"
if (Test-Path $requirementsPath) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r $requirementsPath
} else {
    Write-Error "requirements.txt not found"
    exit 1
}

# Show help
if ($Help) {
    Write-Host @"
Flexible Agents MCP Server - PowerShell Launcher

Usage:
  .\run-server.ps1 [options]

Options:
  -Config <path>      Configuration file path (default: config.json)
  -Debug              Enable debug mode
  -CreateConfig       Create sample configuration files
  -ValidateConfig     Validate configuration
  -ListTools          List all available tools
  -Help               Show this help message

Examples:
  .\run-server.ps1                    # Start server with default config
  .\run-server.ps1 -Debug             # Start server in debug mode
  .\run-server.ps1 -CreateConfig      # Create sample config files
  .\run-server.ps1 -ValidateConfig    # Validate configuration

Environment Variables:
  Set these in your system or create a .env file:
  - AZURE_TENANT_ID
  - AZURE_CLIENT_ID
  - AZURE_CLIENT_SECRET
  - ANTHROPIC_API_KEY

"@
    exit 0
}

# Build arguments
$scriptArgs = @("server.py", "--config", $Config)

if ($Debug) {
    $scriptArgs += "--debug"
}

if ($CreateConfig) {
    $scriptArgs = @("server.py", "--create-config")
}

if ($ValidateConfig) {
    $scriptArgs = @("server.py", "--validate-config", "--config", $Config)
}

if ($ListTools) {
    $scriptArgs = @("server.py", "--list-tools", "--config", $Config)
}

# Run the server
try {
    Write-Host "Starting Flexible Agents MCP Server..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    python @scriptArgs
} catch {
    Write-Error "Failed to start server: $_"
    exit 1
} finally {
    Write-Host ""
    Write-Host "Server stopped" -ForegroundColor Yellow
}
