# Claude Computer Use API - Comprehensive Guide

This guide provides in-depth information about setting up, using, and extending the Claude Computer Use API implementation for Windows 11 systems.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Using the API](#using-the-api)
6. [GUI Interface](#gui-interface)
7. [Extension System](#extension-system)
8. [Security Considerations](#security-considerations)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Usage](#advanced-usage)

## Introduction

The Claude Computer Use API allows Claude to control and interact with your computer through a set of tools designed to enable:

- **Keyboard and mouse control** for application interaction
- **Screenshot capabilities** for visual feedback
- **File system operations** for creating and editing files
- **Command execution** for running system commands
- **Extension system** for adding custom functionality

This implementation provides a streamlined, easy-to-use interface optimized for Windows 11 systems, with a focus on security, performance, and extensibility.

## Architecture Overview

The implementation consists of several key components:

### Core Components

- **`computer_use_api.py`**: Core API implementation with tool definitions
- **`api_integration.py`**: Handles interaction with the Anthropic API
- **`extension_module.py`**: Manages the extension system
- **`gui_wrapper.py`**: Provides a graphical user interface

### Directory Structure

```
C:\Claude-Computer-API\

   computer_use_api.py         # Core API implementation
   extension_module.py         # Extension system
   api_integration.py          # Integration module
   gui_wrapper.py              # GUI application
   quick_setup.py              # Setup script

   config\                     # Configuration files
      settings.json           # Main configuration file

   extensions\                 # Built-in extensions
      web_search.py           # Web search extension
      text_to_speech.py       # Text-to-speech extension
      sample-extension.py     # Example extension template

   custom_extensions\          # Your custom extensions
      app_tracker.py          # Application usage tracking extension

   data\                       # Data storage for extensions
   logs\                       # Log files
   outputs\                    # Screenshots and other outputs
       screenshots\            # Captured screenshots
```

### Communication Flow

1. User interacts with the GUI or CLI
2. Request is processed by the application
3. API request is sent to Anthropic via `api_integration.py`
4. Claude responds with tool calls
5. Tool calls are executed by `computer_use_api.py`
6. Results are returned to Claude
7. Claude provides a response, which is displayed to the user

## Installation

### Prerequisites

- Windows 11 (build 26100.3194 or later)
- Python 3.9+ installed
- Anthropic API key with Computer Use permissions
- Claude 3.5 Sonnet model access
- Administrative privileges (for initial setup)

### Automatic Installation

The easiest way to set up the Computer Use API is to use the provided setup script:

1. Download the repository
2. Open PowerShell as Administrator
3. Navigate to the repository directory
4. Run the setup script:

```powershell
.\final-setup-script.ps1
```

This script will:
- Create the necessary directory structure
- Install required Python packages
- Configure environment variables
- Set up Docker if requested

### Manual Installation

If you prefer to set up manually:

1. Create a project directory:
   ```powershell
   mkdir C:\Claude-Computer-API
   cd C:\Claude-Computer-API
   ```

2. Set up a virtual environment:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install required packages:
   ```powershell
   pip install anthropic pyautogui httpx pillow pyttsx3 requests psutil pygetwindow win10toast python-dotenv tk streamlit
   ```

4. Create the required directories:
   ```powershell
   mkdir config extensions custom_extensions data logs outputs
   ```

5. Copy the source files to appropriate locations.

6. Set your Anthropic API key:
   ```powershell
   setx ANTHROPIC_API_KEY "your_api_key_here"
   ```

### Docker Installation

To use the Docker container:

1. Ensure Docker Desktop is installed on your Windows 11 system
2. Clone the repository
3. Run the Docker Compose command:

```powershell
docker-compose up -d
```

This will:
- Build the container with all necessary dependencies
- Mount the appropriate volumes for data persistence
- Expose the required ports for the interface

## Configuration

### Configuration Files

The main configuration file is `config/settings.json`, which controls all aspects of the application:

- API settings (model, tokens, temperature)
- Security settings (permission levels, restrictions)
- GUI settings (appearance, behavior)
- Extension settings (enabled extensions, paths)
- Tool settings (parameters for each tool)

### Environment Variables

You can use environment variables to override configuration settings:

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `CLAUDE_MODEL`: Claude model to use
- `SECURITY_LEVEL`: Security level setting
- `DEBUG_MODE`: Enable/disable debug mode

These can be set in the `.env` file or in your system environment.

### Security Levels

Three security levels are available:

- **Low**: Minimal restrictions, suitable for trusted environments
- **Medium**: Balanced security with confirmation for sensitive operations
- **High**: Strict security with explicit approval for all operations

Configure the security level in `config/settings.json` or via environment variables.

## Using the API

### Core Tools

The API provides several core tools:

#### Computer Tool

For keyboard, mouse, and screenshot operations:

```python
# Example tool use
{
  "name": "computer",
  "input": {
    "action": "click",
    "x": 500,
    "y": 300
  }
}
```

Actions include:
- `click`: Click at specific coordinates
- `type`: Type text
- `press`: Press a key combination
- `move`: Move the mouse
- `screenshot`: Take a screenshot
- `getWindowInfo`: Get information about windows

#### Command Tool

For executing system commands:

```python
# Example tool use
{
  "name": "command",
  "input": {
    "command": "dir"
  }
}
```

#### File Tool

For file operations:

```python
# Example tool use
{
  "name": "file",
  "input": {
    "action": "read",
    "path": "C:\\path\\to\\file.txt"
  }
}
```

Actions include:
- `read`: Read file content
- `write`: Write content to a file
- `append`: Append content to a file
- `delete`: Delete a file
- `list`: List files in a directory

### Command-Line Interface

You can use the API via command line:

```powershell
python computer_use_api.py
```

This will start a CLI session where you can interact with Claude.

## GUI Interface

The GUI interface provides a user-friendly way to interact with Claude:

### Features

- Chat history display
- Screenshot viewer
- Command input field
- Security controls
- Extension management

### Starting the GUI

Launch the GUI with:

```powershell
python gui_wrapper.py
```

This will open the GUI window where you can immediately start interacting with Claude.

### Interface Controls

- **Chat Input**: Type messages at the bottom
- **Screenshot Panel**: View the latest screenshot
- **Security Controls**: Change security level and permissions
- **Extension Menu**: Enable/disable and configure extensions

## Extension System

The extension system allows you to add custom functionality to the API.

### Built-In Extensions

Several extensions are included:

- **Web Search**: Search the internet and retrieve information
- **Text-to-Speech**: Convert text to speech
- **App Tracker**: Track application usage

### Using Extensions

Extensions can be used with special commands:

```
/ext list
/ext help
/ext web_search query="Claude AI capabilities"
/ext text_to_speech text="Hello, world!" rate=150
```

### Creating Custom Extensions

To create a custom extension:

1. Create a new Python file in the `custom_extensions` directory
2. Inherit from the `Extension` base class
3. Implement the required methods

Example extension:

```python
from extension_module import Extension

class MyCustomExtension(Extension):
    name = "my_custom"
    description = "My custom extension"
    version = "1.0.0"
    author = "Your Name"
    
    async def execute(self, command="default", **kwargs):
        # Implement your functionality here
        return {"result": "Custom extension executed!", "success": True}
```

## Security Considerations

### Risk Mitigation

Since Claude controls your computer, consider these security measures:

1. **Use appropriate security levels**: Adjust based on your environment
2. **Monitor Claude's actions**: Keep an eye on what Claude is doing
3. **Run in a limited account**: Use a non-administrator account
4. **Use a virtual machine**: For maximum isolation
5. **Enable command confirmation**: Verify commands before execution

### Security Features

The implementation includes several security features:

- **Command whitelisting/blacklisting**: Control which commands can be executed
- **Path restrictions**: Limit file access to specific directories
- **Confirmation dialogs**: Require approval for sensitive operations
- **Action logging**: Keep track of all actions performed

## Performance Optimization

### System Requirements

For optimal performance:

- 4+ CPU cores (8+ recommended)
- 16GB+ RAM
- SSD storage
- Dedicated GPU (for GUI features)

### Configuration Tuning

Optimize performance in `config/settings.json`:

- Adjust `memory_limit_mb` based on your system
- Set `max_concurrent_tasks` to match your CPU cores
- Tune `screenshot_throttle_ms` for screenshot frequency

### Docker Optimization

For Docker deployments:

- Adjust resource limits in `docker-compose.yml`
- Use volume mounts for data persistence
- Enable GPU acceleration if available

## Troubleshooting

### Common Issues

#### API Connection Problems

If you encounter API connection issues:

1. Verify your API key is correct
2. Check your internet connection
3. Ensure you have access to the correct Claude model
4. Check the logs for specific error messages

#### GUI Display Issues

For GUI problems:

1. Update your graphics drivers
2. Try switching to a different theme in settings
3. Adjust font size and window dimensions
4. Run with admin privileges for accessibility features

#### Extension Errors

If extensions fail to load:

1. Check the extension logs
2. Verify all dependencies are installed
3. Ensure the extension is compatible with your version
4. Try disabling other extensions for conflicts

### Logs

Check these log files for troubleshooting:

- `logs/computer_use_api.log`: Main API logs
- `logs/api_integration.log`: API communication logs
- `logs/extensions.log`: Extension system logs
- `logs/[extension_name].log`: Individual extension logs

## Advanced Usage

### API Customization

You can customize the API behavior:

- Implement custom tool handlers
- Create specialized system prompts
- Develop domain-specific extensions

### Automation Integration

Integrate with automation systems:

```python
# Example of programmatic API use
from computer_use_api import ComputerUseAPI

api = ComputerUseAPI()
response = api.execute_command("open notepad")
```

### Multi-Model Support

The implementation supports different Claude models:

- Set the model in `config/settings.json`
- Models include `claude-3-opus`, `claude-3-sonnet`, and `claude-3-5-sonnet`
- Different models have varying capabilities and performance

### Docker Compose Configuration

Advanced Docker settings:

```yaml
# Custom Docker configuration
services:
  claude-computer-api:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./config:/app/config:ro
      - ./data:/app/data
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
```

Adjust resources based on your system capabilities.

## Contributing

Contributions to this implementation are welcome! Please feel free to submit pull requests or open issues on the repository.

When contributing:

1. Follow the coding style of existing files
2. Add appropriate documentation
3. Include tests for new functionality
4. Update the changelog with your changes

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

**Note**: This implementation is not officially affiliated with or endorsed by Anthropic. Always use the Computer Use API responsibly and in accordance with Anthropic's terms of service.