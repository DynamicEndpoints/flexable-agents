\
<!-- filepath: c:\\Users\\Owner\\flexable-agents\\README.md -->
# Flexible Agents MCP Server

A robust, AI-powered Model Context Protocol (MCP) server built with Python, FastAPI, and Pydantic. This system provides a standardized interface for exposing various tools (formerly agents) for AI models, including capabilities for Microsoft 365 integration, content generation, data processing, and more.

## 🌟 Features

*   **MCP Compliance**: Fully compliant with the Model Context Protocol for standardized AI tool interaction.
*   **Extensible Toolset**: Easily add new tools and capabilities.
    *   **Microsoft 365 Core Tools**: Interact with M365 services (Outlook, SharePoint, Teams, etc.).
    *   **Specialized Tools**: Azure management, document processing (PDF, DOCX, OCR), data analysis.
    *   **Workflow Tools**: Orchestrate complex multi-step operations.
*   **Structured Logging**: Comprehensive logging with Rich console output and JSON/detailed file logs.
*   **Performance Monitoring**: Real-time monitoring of server health, performance, and error metrics.
*   **Configuration Management**: Flexible configuration via `config.json` and environment variables.
*   **Command Line Interface (CLI)**: Utilities for server management, configuration validation, tool listing, and testing.
*   **Async Architecture**: Built with FastAPI and `asyncio` for high performance.
*   **Microsoft Graph API Integration**: Seamlessly connect and interact with Microsoft Graph.
*   **Anthropic Claude Integration**: Leverages Claude models for advanced AI tasks (configurable).

## 🚀 Getting Started

### Prerequisites

*   Python 3.9+
*   Pip (Python package installer)
*   Access to necessary cloud services if using corresponding tools (e.g., Azure subscription, M365 tenant).

### Environment Setup

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd flexible-agents-mcp
    ```

2.  **Create a Virtual Environment** (recommended):
    ```bash
    python -m venv .venv
    ```
    Activate the virtual environment:
    *   Windows (pwsh): `.\\.venv\\Scripts\\Activate.ps1`
    *   Windows (cmd): `.\\.venv\\Scripts\\activate.bat`
    *   Linux/macOS: `source ./.venv/bin/activate`

3.  **Install Dependencies**:
    The project uses `pyproject.toml` for managing dependencies.
    ```bash
    pip install . 
    ```
    For development, including tools for testing and linting:
    ```bash
    pip install -r requirements-dev.txt
    ```

4.  **Configuration Files**:
    *   **Main Configuration (`config.json`)**:
        *   Copy `config.json.example` to `config.json` in the root directory.
            ```powershell
            Copy-Item config.json.example config.json
            ```
        *   Edit `config.json` to provide your specific settings:
            *   `m365`: `tenant_id`, `client_id`, `client_secret` for Microsoft Graph API access.
            *   `anthropic`: `api_key` for Anthropic Claude models.
            *   `azure`: `subscription_id`, `resource_group` if using Azure tools.
            *   `server`: Adjust server settings like `log_level`, `debug` mode if needed.
    *   **Environment Variables (`.env`)**:
        *   Sensitive information like API keys or secrets can also be placed in a `.env` file in the root directory. Copy `.env.example` to `.env` and fill in the values.
            ```powershell
            Copy-Item .env.example .env
            ```
        *   Values in `.env` will override those in `config.json` if both are present for the same setting (e.g., `ANTHROPIC_API_KEY`).
            Example `.env` content:
            ```env
            AZURE_TENANT_ID="your-tenant-id"
            AZURE_CLIENT_ID="your-client-id"
            AZURE_CLIENT_SECRET="your-client-secret"
            ANTHROPIC_API_KEY="your-anthropic-api-key"
            AZURE_SUBSCRIPTION_ID="your-azure-subscription-id"
            ```

### Running the MCP Server

You can run the server in several ways:

1.  **Directly with `server.py`**:
    ```bash
    python server.py --config config.json --port 8000
    ```
    Use `--debug` for more verbose output during development.

2.  **Using the CLI**:
    ```bash
    python -m src.cli server --config config.json --port 8000
    ```

3.  **Using Provided Scripts**:
    *   Windows PowerShell: `.\\run-server.ps1`
    *   Windows Batch: `.\\run-server.bat`
    These scripts typically run the server with default settings. You might need to edit them if your `config.json` is not in the default location or if you want to specify a different port.

Once the server is running, it will typically be accessible at `http://localhost:8000` (or the port you specified). The MCP manifest will be available at `http://localhost:8000/mcp.json`.

## ⚙️ MCP Server Usage

The Flexible Agents MCP Server exposes its tools according to the Model Context Protocol. AI models or other MCP clients can interact with the server by making HTTP requests to its defined endpoints.

*   **Manifest**: The server's capabilities are described in the manifest file, typically available at the `/mcp.json` endpoint (e.g., `http://localhost:8000/mcp.json`).
*   **Tool Calls**: To execute a tool, an MCP client sends a `POST` request to the `/tool/{tool_name}` endpoint.

**Example MCP Request (conceptual):**

A client wanting to use the `M365_Calendar_Create_Event` tool would send a POST request to `http://localhost:8000/tool/M365_Calendar_Create_Event` with a JSON body like:

```json
{
  "contextId": "unique-context-id",
  "invocationId": "unique-invocation-id",
  "toolName": "M365_Calendar_Create_Event",
  "arguments": {
    "subject": "Team Meeting",
    "start_time": "2025-06-16T10:00:00",
    "end_time": "2025-06-16T11:00:00",
    "attendees": ["user1@example.com", "user2@example.com"],
    "body": "Discuss project updates."
  }
}
```

**Example MCP Response (conceptual):**

The server would respond with:

```json
{
  "contextId": "unique-context-id",
  "invocationId": "unique-invocation-id",
  "toolName": "M365_Calendar_Create_Event",
  "isError": false,
  "content": [
    {
      "type": "application/json",
      "content": {
        "event_id": "AAMkAGYz...=",
        "subject": "Team Meeting",
        "start": "2025-06-16T10:00:00Z",
        "end": "2025-06-16T11:00:00Z",
        "attendees": ["user1@example.com", "user2@example.com"],
        "message": "Event created successfully"
      }
    }
  ]
}
```
If an error occurs, `isError` would be `true`, and the `content` would typically contain error details.

## 🛠️ Available Tools

The server comes with a variety of pre-built tools. You can list all available tools using the CLI: `python -m src.cli list-tools`.

Here are some of the categories and example tools:

*   **Microsoft 365 Tools (`src/tools/m365_tools.py`)**:
    *   `M365_Calendar_Create_Event`: Creates a new calendar event.
    *   `M365_Calendar_List_Events`: Lists calendar events.
    *   `M365_Email_Send`: Sends an email.
    *   `M365_Email_List_Messages`: Lists emails from the inbox.
    *   `M365_SharePoint_List_Sites`: Lists SharePoint sites.
    *   `M365_SharePoint_Search_Files`: Searches for files in SharePoint.
    *   `M365_Teams_Send_Message`: Sends a message to a Teams channel.
    *   *(Many more...)*
*   **Azure Tools (`src/tools/azure_tools.py`)**:
    *   `Azure_VM_List`: Lists virtual machines.
    *   `Azure_Resource_Group_List`: Lists resource groups.
*   **Document Tools (`src/tools/document_tools.py`)**:
    *   `Document_Extract_Text_PDF`: Extracts text from a PDF file.
    *   `Document_Extract_Text_DOCX`: Extracts text from a DOCX file.
    *   `Document_OCR_Image`: Performs OCR on an image to extract text.
*   **Data Tools (`src/tools/data_tools.py`)**:
    *   `Data_Analyze_CSV`: Performs basic analysis on a CSV file.
*   **Specialized Tools (`src/tools/specialized_tools.py`)**:
    *   `Claude_Generate_Text`: Generates text using an Anthropic Claude model.
*   **Workflow Tools (`src/tools/workflow_tools.py`)**:
    *   Tools for orchestrating sequences of other tool calls.

Each tool has defined input parameters and output formats, as specified in their implementation and discoverable via the MCP manifest or by inspecting the tool registration in the respective Python modules.

## ⌨️ Command Line Interface (CLI)

The CLI (`src/cli.py`) provides several utilities for managing and interacting with the MCP server. Access it using `python -m src.cli`.

**Common Commands:**

*   `python -m src.cli --help`: Shows all available commands.
*   `python -m src.cli server [OPTIONS]`: Starts the MCP server.
    *   `--config TEXT`: Path to the configuration file (default: `config.json`).
    *   `--host TEXT`: Host to bind the server to (default: `0.0.0.0`).
    *   `--port INTEGER`: Port to run the server on (default: `8000`).
    *   `--debug / --no-debug`: Enable or disable debug mode.
    *   `--health-check`: Performs a server health check and exits.
*   `python -m src.cli list-tools [OPTIONS]`: Lists all registered tools.
    *   `--config TEXT`: Path to the configuration file.
*   `python -m src.cli test-tool <TOOL_NAME> [PARAMETERS] [OPTIONS]`: Tests a specific tool.
    *   `<TOOL_NAME>`: The name of the tool to test (e.g., `M365_Email_List_Messages`).
    *   `[PARAMETERS]`: Optional JSON string of parameters for the tool (e.g., `'{"folder_name": "Inbox", "count": 5}'`).
    *   `--config TEXT`: Path to the configuration file.
*   `python -m src.cli validate-config [OPTIONS]`: Validates the configuration file.
    *   `--config TEXT`: Path to the configuration file.
*   `python -m src.cli create-config`: Creates sample configuration files (`config.json.example`, `.env.example`).
*   `python -m src.cli show-config [OPTIONS]`: Shows the current configuration (masks sensitive values).
    *   `--config TEXT`: Path to the configuration file.

**Example CLI Usage:**

```bash
# Start the server with a specific config and port
python -m src.cli server --config my_config.json --port 8080

# List all available tools
python -m src.cli list-tools

# Test the M365_Email_List_Messages tool
python -m src.cli test-tool M365_Email_List_Messages '{"count": 3}'

# Validate your config.json
python -m src.cli validate-config --config config.json 
```

## ⚙️ Configuration

The server's behavior is primarily controlled by `config.json`.

*   **`server`**: General server settings (name, version, debug mode, log level, timeout).
*   **`m365`**: Microsoft 365 connection details (tenant ID, client ID, client secret, scopes).
*   **`anthropic`**: Anthropic API settings (API key, model, max tokens, temperature).
*   **`azure`**: Azure connection details (subscription ID, resource group, default location).

Refer to `config.json.example` for the structure and available options.

## 🧑‍💻 Development

### Project Structure

*   `server.py`: Main entry point for the FastAPI MCP server.
*   `src/cli.py`: Command Line Interface.
*   `src/mcp/`: Core MCP handling logic (server, handlers, registry, types, logging).
*   `src/tools/`: Directory containing all MCP tool implementations (e.g., `m365_tools.py`, `azure_tools.py`).
*   `src/core/`: Base classes and utilities.
*   `config.json`: Server configuration file.
*   `mcp.json`: MCP manifest file (generated based on registered tools).

### Adding a New Tool

1.  **Create or Choose a Module**: Place your tool logic in an appropriate file within `src/tools/` (e.g., `my_new_tools.py`).
2.  **Implement the Tool Function**:
    *   The function should be `async def`.
    *   Use type hints for parameters.
    *   The function should return a dictionary or a Pydantic model that can be serialized to JSON. This will form the `content` part of the MCP response.
    *   Incorporate error handling. The `with_error_handling` decorator from `src/mcp/handlers.py` can be used for standardized error responses.
3.  **Register the Tool**:
    *   In your tool module, use the `@tool` decorator from `src/mcp/registry.py` or manually register tools with an instance of `ToolRegistry`.
    *   Ensure your tool module is imported and its tools are registered in `src/tools/__init__.py` within the `register_all_tools` function.
    *   Provide a clear `name`, `description`, and define `parameters` (if not auto-detected from type hints) and `returns` for the tool metadata.

**Example Tool Snippet (in `src/tools/my_new_tools.py`):**
```python
from src.mcp.registry import tool
from src.mcp.handlers import with_error_handling, log_request_metrics
import time

@tool(
    name="MyTool_Echo",
    description="A simple tool that echoes back the input message.",
    parameters=[{"name": "message", "type": "string", "description": "The message to echo.", "required": True}],
    returns="A JSON object containing the echoed message."
)
@with_error_handling("MyTool_Echo") # For standardized error handling
async def my_echo_tool(message: str) -> dict:
    start_time = time.time()
    success = True
    error_message = None
    try:
        # Your tool logic here
        if not message:
            raise ValueError("Message cannot be empty.")
        result = {"echo": message, "received_at": time.time()}
        return result
    except Exception as e:
        success = False
        error_message = str(e)
        # The with_error_handling decorator will catch this and format it
        raise 
    finally:
        duration = time.time() - start_time
        log_request_metrics(method="MyTool_Echo", duration=duration, success=success, error=error_message)

```
4.  **Update `src/tools/__init__.py`**:
    ```python
    # In src/tools/__init__.py
    # ... other imports ...
    from . import my_new_tools # Import your new module

    def register_all_tools(server, config_manager):
        # ... existing tool registrations ...
        my_new_tools.register_tools(server.tool_registry, config_manager) # Assuming you have a register_tools func in your module
        # Or, if using the @tool decorator and auto-registration from module:
        # from src.mcp.registry import register_tools_from_module
        # register_tools_from_module(server.tool_registry, my_new_tools)
    ```

### Logging and Error Handling

*   The system uses the `logging_system.py` for structured logging. Use the standard `logging` module in your tools; it will be processed by `structlog`.
*   The `log_request_metrics` function from `src.mcp.logging_system` should be called to record tool execution success/failure and duration.
*   The `with_error_handling` decorator in `src.mcp.handlers` provides a standardized way to catch exceptions in tools and format them as MCP error responses.

## 📝 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🙏 Acknowledgments

*   FastAPI, Pydantic, Structlog, Rich
*   Anthropic for Claude models
*   Microsoft for Graph API and Azure SDKs
*   The open-source community

## 🔮 Future Enhancements (Planned / Ideas)

*   **Enhanced Workflow Orchestration**: More sophisticated built-in tools for managing complex, multi-step workflows.
*   **Dynamic Tool Registration**: Allow tools to be registered/unregistered at runtime.
*   **Improved Security**: OAuth2/OpenID Connect for server endpoints.
*   **User Management/Authentication for Tools**: Per-user permissions or context for tool execution.
*   **Web UI for Management**: A simple web interface for server status, tool management, and log viewing.
*   **Containerization**: Dockerfile and docker-compose for easy deployment.
*   **Comprehensive Test Suite**: Expand test coverage for all tools and core components.

---

*This README has been updated to reflect the transition to an MCP server architecture.*
