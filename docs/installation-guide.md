# Optimized Computer Use API - Installation and Usage Guide

This guide will help you set up and run the optimized Computer Use API implementation on your Windows 11 system with Intel i3-1215U processor.

## Prerequisites

- Windows 11 (build 26100.3194 or later)
- Python 3.9+ installed
- Administrative privileges (for installing required packages)

## Installation

1. **Create a project directory**

```bash
mkdir computer-use-api
cd computer-use-api
```

2. **Set up a virtual environment (recommended)**

```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install required packages**

```bash
pip install anthropic pyautogui httpx
```

4. **Save the implementation code**

Copy the provided Python implementation into a file named `computer_use_api.py`.

5. **Set up your Anthropic API key**

You can set it as an environment variable:

```bash
set ANTHROPIC_API_KEY=your_api_key_here
```

Or modify the code to directly use your API key.

## Directory Structure

Ensure you have the following directory structure:

```
computer-use-api/
├── computer_use_api.py
├── outputs/       # Created automatically for saving screenshots
└── config/        # Created automatically for configuration
```

## Usage

### Running the API

You can use the API in two ways:

#### 1. Using the built-in command line interface

```bash
python computer_use_api.py
```

This will prompt you to enter a command, which will be sent to Claude.

#### 2. Importing the API in your own code

```python
import asyncio
from computer_use_api import ComputerUseAPI

async def run_example():
    # Initialize the API with your API key
    api = ComputerUseAPI("your_api_key_here")
    
    # Define callback functions
    def output_callback(content):
        if content["type"] == "text":
            print(f"Assistant: {content['text']}")
        elif content["type"] == "tool_use":
            print(f"Tool use: {content['name']}")
    
    def tool_output_callback(result, tool_id):
        if result.output:
            print(f"Tool output: {result.output}")
        if result.error:
            print(f"Tool error: {result.error}")
    
    def api_response_callback(request, response, error):
        if error:
            print(f"API error: {error}")
    
    # Run a conversation
    await api.run_conversation(
        "Open Notepad and type 'Hello, World!'",
        output_callback,
        tool_output_callback,
        api_response_callback,
    )

# Run the example
asyncio.run(run_example())
```

## Tool Capabilities

This implementation includes several tools:

### 1. Computer Tool

Controls screen, keyboard, and mouse. Actions include:

- `screenshot`: Take a screenshot
- `key`: Press keyboard keys
- `type`: Type text
- `mouse_move`: Move mouse cursor
- `left_click`: Perform left click
- `right_click`: Perform right click
- `middle_click`: Perform middle click
- `double_click`: Perform double click
- `left_click_drag`: Click and drag the mouse
- `cursor_position`: Get current cursor position

### 2. Command Tool

Executes command-line commands:

- Run any Windows command prompt commands
- Maximum execution time: 60 seconds

### 3. File Tool

Manages files on the system:

- `view`: View file contents
- `create`: Create a new file
- `str_replace`: Replace text in a file
- `insert`: Insert text at a specific line
- `undo_edit`: Undo the last edit

## Security Considerations

- This implementation gives Claude direct access to your computer
- Be cautious about the commands and access you allow
- Monitor the operations to ensure nothing harmful occurs
- Avoid giving access to sensitive information or systems

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure your Anthropic API key is correctly set and has Computer Use permissions
   - Verify your Anthropic account has access to the Claude 3.5 Sonnet model
   - Check if you have the correct beta access for computer-use features

2. **Screen Interaction Issues**
   - Some applications may have security features preventing automation
   - Try running the script with administrator privileges
   - Ensure your display scaling is set to 100% for more accurate coordinates

3. **Command Tool Errors**
   - Windows security may block some commands; check your Windows Security settings
   - Some commands require elevation; try prefixing with appropriate permissions
   - Long-running commands might time out; consider increasing the timeout value

4. **Import Errors**
   - If you see errors about missing packages, ensure all required packages are installed
   - Try installing packages individually: `pip install anthropic`, `pip install pyautogui`, etc.

5. **Permission Errors**
   - File operations may fail due to permission issues in protected directories
   - Try using paths within your user directory

## Performance Optimization

Since you're running on an Intel i3-1215U with 32GB RAM, here are some specific optimizations:

1. **Adjust Screenshot Resolution**
   - Modify the ComputerTool class to use a lower resolution for screenshots if needed
   - This reduces memory usage and processing time

2. **Command Execution**
   - For CPU-intensive operations, consider using the async capabilities more effectively
   - The large RAM capacity allows for processing multiple screenshots without clearing them

3. **Memory Management**
   - The implementation already keeps screenshot history minimal, but you can further reduce it
   - Modify the `_screenshot_delay` value based on your system's performance

## Example Script

Here's a complete example script to get you started:

```python
# example_script.py
import asyncio
import os
from computer_use_api import ComputerUseAPI, ToolResult

# Callbacks for handling API responses
def handle_assistant_output(content):
    """Process content from the assistant."""
    if content["type"] == "text":
        print(f"\n🤖 Claude: {content['text']}")
    elif content["type"] == "tool_use":
        tool_name = content["name"]
        tool_input = content["input"]
        print(f"\n🔧 Using tool: {tool_name}")
        print(f"   Input: {tool_input}")

def handle_tool_output(result: ToolResult, tool_id: str):
    """Process outputs from tools."""
    if result.output:
        print(f"\n📤 Tool output: {result.output}")
    if result.error:
        print(f"\n❌ Tool error: {result.error}")
    if result.base64_image:
        print("\n🖼️ Screenshot captured")

def handle_api_response(request, response, error):
    """Handle API responses and errors."""
    if error:
        print(f"\n⚠️ API error: {str(error)}")

async def run_computer_task(task_description):
    """Run a computer task using Claude."""
    # Get API key from environment or input
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = input("Enter your Anthropic API key: ")
        
    # Initialize the API
    api = ComputerUseAPI(api_key)
    
    # Run the conversation
    print(f"\n📝 Task: {task_description}")
    print("\nStarting conversation with Claude...\n")
    
    try:
        await api.run_conversation(
            task_description,
            handle_assistant_output,
            handle_tool_output,
            handle_api_response
        )
        print("\n✅ Task completed!")
    except Exception as e:
        print(f"\n❌ Error running task: {str(e)}")

if __name__ == "__main__":
    # Example task
    task = "Open Notepad, type 'Hello from Claude!', take a screenshot, and then close Notepad."
    
    # Run the task
    asyncio.run(run_computer_task(task))
```

To use this example, save it as `example_script.py` and run:

```bash
python example_script.py
```

This will execute a simple task that demonstrates the core functionality of the Computer Use API.