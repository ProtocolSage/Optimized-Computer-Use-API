import asyncio
import base64
import os
import platform
import subprocess
import time
from collections.abc import Callable
from datetime import datetime
from enum_compat import StrEnum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict, Union, cast

import httpx
from anthropic import Anthropic, APIError, APIResponseValidationError, APIStatusError
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

# Constants
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
MODEL_NAME = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 4096
OUTPUT_DIR = Path("./outputs")
CONFIG_DIR = Path("./config")

# System prompt
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilizing a Windows 11 computer with {platform.machine()} architecture and internet access.
* You can open applications installed on the system.
* When viewing a webpage, make sure to scroll down to see everything before deciding something isn't available.
* The current date is {datetime.today().strftime('%A, %B %d, %Y')}.
* This computer has a 12th Gen Intel(R) Core(TM) i3-1215U processor and 32GB of RAM.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using a browser, make sure to look at the entire page before making conclusions.
* Try to be efficient with your actions to accomplish the user's goals.
</IMPORTANT>"""

# Tool Result class
class ToolResult:
    """Represents the result of a tool execution."""
    
    def __init__(self, output: Optional[str] = None, error: Optional[str] = None, 
                 base64_image: Optional[str] = None, system: Optional[str] = None):
        self.output = output
        self.error = error
        self.base64_image = base64_image
        self.system = system

    def __bool__(self):
        return any([self.output, self.error, self.base64_image, self.system])
        
    def replace(self, **kwargs):
        """Returns a new ToolResult with the given fields replaced."""
        result = ToolResult(
            output=self.output,
            error=self.error,
            base64_image=self.base64_image,
            system=self.system
        )
        for k, v in kwargs.items():
            setattr(result, k, v)
        return result

# Computer Tool
class ComputerAction(StrEnum):
    KEY = "key"
    TYPE = "type"
    MOUSE_MOVE = "mouse_move"
    LEFT_CLICK = "left_click"
    LEFT_CLICK_DRAG = "left_click_drag"
    RIGHT_CLICK = "right_click"
    MIDDLE_CLICK = "middle_click"
    DOUBLE_CLICK = "double_click"
    SCREENSHOT = "screenshot"
    CURSOR_POSITION = "cursor_position"

class ComputerTool:
    """Tool that allows interaction with the screen, keyboard, and mouse."""
    
    name = "computer"
    api_type = "computer_20241022"
    
    def __init__(self):
        self.width = 1920
        self.height = 1080
        self._screenshot_delay = 1.0
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Windows-specific imports for UI automation
        try:
            import pyautogui
            self.pyautogui = pyautogui
        except ImportError:
            print("Installing pyautogui...")
            subprocess.check_call(["pip", "install", "pyautogui"])
            import pyautogui
            self.pyautogui = pyautogui

    def to_params(self):
        return {
            "name": self.name,
            "type": self.api_type,
            "display_width_px": self.width,
            "display_height_px": self.height,
            "display_number": None,
        }
        
    async def __call__(self, *, action: str, text: Optional[str] = None, 
                     coordinate: Optional[List[int]] = None, **kwargs):
        """Execute a computer action."""
        
        if action in (ComputerAction.MOUSE_MOVE, ComputerAction.LEFT_CLICK_DRAG):
            if coordinate is None:
                return ToolResult(error=f"coordinate is required for {action}")
            if text is not None:
                return ToolResult(error=f"text is not accepted for {action}")
            
            x, y = coordinate[0], coordinate[1]
            
            if action == ComputerAction.MOUSE_MOVE:
                self.pyautogui.moveTo(x, y)
                return await self.take_screenshot(f"Mouse moved to {x}, {y}")
            elif action == ComputerAction.LEFT_CLICK_DRAG:
                current_x, current_y = self.pyautogui.position()
                self.pyautogui.mouseDown(current_x, current_y, button='left')
                self.pyautogui.moveTo(x, y)
                self.pyautogui.mouseUp(x, y, button='left')
                return await self.take_screenshot(f"Mouse dragged from {current_x},{current_y} to {x},{y}")
                
        if action in (ComputerAction.KEY, ComputerAction.TYPE):
            if text is None:
                return ToolResult(error=f"text is required for {action}")
            if coordinate is not None:
                return ToolResult(error=f"coordinate is not accepted for {action}")
                
            if action == ComputerAction.KEY:
                self.pyautogui.hotkey(*text.split('+'))
                return await self.take_screenshot(f"Pressed key: {text}")
            elif action == ComputerAction.TYPE:
                self.pyautogui.write(text, interval=0.01)
                return await self.take_screenshot(f"Typed: {text}")
                
        if action in (ComputerAction.LEFT_CLICK, ComputerAction.RIGHT_CLICK, 
                      ComputerAction.MIDDLE_CLICK, ComputerAction.DOUBLE_CLICK, 
                      ComputerAction.SCREENSHOT, ComputerAction.CURSOR_POSITION):
            if text is not None:
                return ToolResult(error=f"text is not accepted for {action}")
            if coordinate is not None and action != ComputerAction.LEFT_CLICK:
                return ToolResult(error=f"coordinate is not accepted for {action}")
                
            if action == ComputerAction.SCREENSHOT:
                return await self.take_screenshot("Screenshot taken")
            elif action == ComputerAction.CURSOR_POSITION:
                x, y = self.pyautogui.position()
                return ToolResult(output=f"X={x},Y={y}")
            else:
                if action == ComputerAction.LEFT_CLICK:
                    if coordinate:
                        x, y = coordinate[0], coordinate[1]
                        self.pyautogui.click(x, y, button='left')
                    else:
                        self.pyautogui.click(button='left')
                elif action == ComputerAction.RIGHT_CLICK:
                    self.pyautogui.click(button='right')
                elif action == ComputerAction.MIDDLE_CLICK:
                    self.pyautogui.click(button='middle')
                elif action == ComputerAction.DOUBLE_CLICK:
                    self.pyautogui.doubleClick()
                
                return await self.take_screenshot(f"Performed {action}")
                
        return ToolResult(error=f"Invalid action: {action}")
        
    async def take_screenshot(self, output_msg=None):
        """Take a screenshot and return as base64."""
        await asyncio.sleep(self._screenshot_delay)
        timestamp = int(time.time())
        path = OUTPUT_DIR / f"screenshot_{timestamp}.png"
        
        screenshot = self.pyautogui.screenshot()
        screenshot.save(path)
        
        if path.exists():
            return ToolResult(
                output=output_msg,
                base64_image=base64.b64encode(path.read_bytes()).decode()
            )
        return ToolResult(error="Failed to take screenshot")

# Command Tool
class CommandTool:
    """Tool that allows running command-line commands."""
    
    name = "command"
    api_type = "bash_20241022"  # Using bash type for compatibility
    
    def __init__(self):
        pass
        
    def to_params(self):
        return {
            "name": self.name,
            "type": self.api_type,
        }
        
    async def __call__(self, command: Optional[str] = None, restart: bool = False, **kwargs):
        """Execute a command line command."""
        if restart:
            return ToolResult(system="Command tool has been restarted.")
            
        if command is None:
            return ToolResult(error="No command provided.")
            
        # Use subprocess to run the command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
            stdout_str = stdout.decode() if stdout else ""
            stderr_str = stderr.decode() if stderr else ""
            
            return ToolResult(
                output=stdout_str if stdout_str else None,
                error=stderr_str if stderr_str else None
            )
        except asyncio.TimeoutError:
            process.kill()
            return ToolResult(error="Command timed out after 60 seconds")

# File Tool
class EditCommand(StrEnum):
    VIEW = "view"
    CREATE = "create"
    STR_REPLACE = "str_replace"
    INSERT = "insert"
    UNDO_EDIT = "undo_edit"

class FileTool:
    """Tool that allows viewing and editing files."""
    
    api_type = "text_editor_20241022"
    name = "str_replace_editor"
    
    def __init__(self):
        self._file_history = {}
        
    def to_params(self):
        return {
            "name": self.name,
            "type": self.api_type,
        }
        
    async def __call__(
        self,
        *,
        command: str,
        path: str,
        file_text: Optional[str] = None,
        view_range: Optional[List[int]] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        insert_line: Optional[int] = None,
        **kwargs,
    ):
        """Execute a file operation."""
        _path = Path(path)
        
        try:
            # Validate path
            if not _path.is_absolute():
                return ToolResult(error=f"The path {path} is not an absolute path, it should start with a drive letter.")
                
            if command == EditCommand.VIEW:
                return await self.view(_path, view_range)
            elif command == EditCommand.CREATE:
                if file_text is None:
                    return ToolResult(error="Parameter `file_text` is required for command: create")
                return self.create(_path, file_text)
            elif command == EditCommand.STR_REPLACE:
                if old_str is None:
                    return ToolResult(error="Parameter `old_str` is required for command: str_replace")
                return self.str_replace(_path, old_str, new_str or "")
            elif command == EditCommand.INSERT:
                if insert_line is None:
                    return ToolResult(error="Parameter `insert_line` is required for command: insert")
                if new_str is None:
                    return ToolResult(error="Parameter `new_str` is required for command: insert")
                return self.insert(_path, insert_line, new_str)
            elif command == EditCommand.UNDO_EDIT:
                return self.undo_edit(_path)
            else:
                return ToolResult(error=f"Unrecognized command {command}.")
        except Exception as e:
            return ToolResult(error=f"Error: {str(e)}")
            
    async def view(self, path: Path, view_range: Optional[List[int]] = None):
        """View a file or directory."""
        if path.is_dir():
            if view_range:
                return ToolResult(error="The `view_range` parameter is not allowed when `path` points to a directory.")
                
            files = []
            for item in path.iterdir():
                if not item.name.startswith('.'):
                    files.append(str(item))
                    
            output = f"Directory listing of {path}:\n" + "\n".join(files)
            return ToolResult(output=output)
            
        if not path.exists():
            return ToolResult(error=f"The path {path} does not exist.")
            
        try:
            file_content = path.read_text()
            
            if view_range:
                if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                    return ToolResult(error="Invalid `view_range`. It should be a list of two integers.")
                    
                lines = file_content.split('\n')
                start, end = view_range
                
                if start < 1 or start > len(lines):
                    return ToolResult(error=f"Invalid start line {start}, should be between 1 and {len(lines)}")
                    
                if end != -1 and (end < start or end > len(lines)):
                    return ToolResult(error=f"Invalid end line {end}, should be between {start} and {len(lines)} or -1")
                    
                if end == -1:
                    file_content = '\n'.join(lines[start-1:])
                else:
                    file_content = '\n'.join(lines[start-1:end])
                    
            # Format with line numbers
            numbered_content = ""
            for i, line in enumerate(file_content.split('\n')):
                numbered_content += f"{i+1:6}\t{line}\n"
                
            return ToolResult(output=f"Contents of {path}:\n{numbered_content}")
        except Exception as e:
            return ToolResult(error=f"Error reading file {path}: {str(e)}")
            
    def create(self, path: Path, file_text: str):
        """Create a new file."""
        if path.exists():
            return ToolResult(error=f"File already exists at: {path}. Cannot overwrite files using command `create`.")
            
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file_text)
            self._file_history[path] = [file_text]
            return ToolResult(output=f"File created successfully at: {path}")
        except Exception as e:
            return ToolResult(error=f"Error creating file {path}: {str(e)}")
            
    def str_replace(self, path: Path, old_str: str, new_str: str):
        """Replace text in a file."""
        if not path.exists():
            return ToolResult(error=f"The path {path} does not exist.")
            
        if path.is_dir():
            return ToolResult(error=f"The path {path} is a directory and cannot be edited.")
            
        try:
            file_content = path.read_text()
            
            # Check for occurrences
            occurrences = file_content.count(old_str)
            if occurrences == 0:
                return ToolResult(error=f"No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}.")
            elif occurrences > 1:
                lines = [i+1 for i, line in enumerate(file_content.split('\n')) if old_str in line]
                return ToolResult(error=f"Multiple occurrences of old_str `{old_str}` in lines {lines}. Please ensure it is unique.")
                
            # Save backup
            if path not in self._file_history:
                self._file_history[path] = []
            self._file_history[path].append(file_content)
            
            # Replace and save
            new_content = file_content.replace(old_str, new_str)
            path.write_text(new_content)
            
            return ToolResult(output=f"The file {path} has been edited. Replaced '{old_str}' with '{new_str}'.")
        except Exception as e:
            return ToolResult(error=f"Error replacing text in {path}: {str(e)}")
            
    def insert(self, path: Path, insert_line: int, new_str: str):
        """Insert text at a specific line in the file."""
        if not path.exists():
            return ToolResult(error=f"The path {path} does not exist.")
            
        if path.is_dir():
            return ToolResult(error=f"The path {path} is a directory and cannot be edited.")
            
        try:
            file_content = path.read_text()
            lines = file_content.split('\n')
            
            if insert_line < 0 or insert_line > len(lines):
                return ToolResult(error=f"Invalid insert_line {insert_line}, should be between 0 and {len(lines)}.")
                
            # Save backup
            if path not in self._file_history:
                self._file_history[path] = []
            self._file_history[path].append(file_content)
            
            # Insert the new text
            new_lines = new_str.split('\n')
            result_lines = lines[:insert_line] + new_lines + lines[insert_line:]
            new_content = '\n'.join(result_lines)
            
            path.write_text(new_content)
            
            return ToolResult(output=f"The file {path} has been edited. Inserted text at line {insert_line}.")
        except Exception as e:
            return ToolResult(error=f"Error inserting text in {path}: {str(e)}")
            
    def undo_edit(self, path: Path):
        """Undo the last edit to a file."""
        if not path.exists():
            return ToolResult(error=f"The path {path} does not exist.")
            
        if path not in self._file_history or not self._file_history[path]:
            return ToolResult(error=f"No edit history found for {path}.")
            
        try:
            previous_content = self._file_history[path].pop()
            path.write_text(previous_content)
            return ToolResult(output=f"Last edit to {path} undone successfully.")
        except Exception as e:
            return ToolResult(error=f"Error undoing edit in {path}: {str(e)}")

# Tool Collection
class ToolCollection:
    """Collection of tools for the assistant to use."""
    
    def __init__(self, *tools):
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}
        
    def to_params(self):
        return [tool.to_params() for tool in self.tools]
        
    async def run(self, *, name: str, tool_input: Dict[str, Any]):
        tool = self.tool_map.get(name)
        if not tool:
            return ToolResult(error=f"Tool {name} is not available")
        try:
            return await tool(**tool_input)
        except Exception as e:
            return ToolResult(error=f"Error executing tool {name}: {str(e)}")

# Main API Client
class ComputerUseAPI:
    """Main client for the Computer Use API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
        self.model = MODEL_NAME
        self.tools = ToolCollection(
            ComputerTool(),
            CommandTool(),
            FileTool(),
        )
        self.system_prompt = SYSTEM_PROMPT
        
    async def run_conversation(
        self,
        user_message: str,
        output_callback: Callable[[BetaContentBlockParam], None],
        tool_output_callback: Callable[[ToolResult, str], None],
        api_response_callback: Callable[[httpx.Request, httpx.Response, Optional[Exception]], None],
    ):
        """Run a conversation with the model."""
        messages = [
            {"role": "user", "content": [{"type": "text", "text": user_message}]}
        ]
        
        return await self._sampling_loop(
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
        )
        
    async def _sampling_loop(
        self,
        *,
        messages: List[BetaMessageParam],
        output_callback: Callable[[BetaContentBlockParam], None],
        tool_output_callback: Callable[[ToolResult, str], None],
        api_response_callback: Callable[[httpx.Request, httpx.Response, Optional[Exception]], None],
    ):
        """Core sampling loop for the assistant/tool interaction."""
        system = {"type": "text", "text": self.system_prompt}
        
        while True:
            try:
                raw_response = self.client.beta.messages.with_raw_response.create(
                    max_tokens=MAX_TOKENS,
                    messages=messages,
                    model=self.model,
                    system=[system],
                    tools=self.tools.to_params(),
                    betas=[COMPUTER_USE_BETA_FLAG],
                )
                
                api_response_callback(
                    raw_response.http_response.request, 
                    raw_response.http_response, 
                    None
                )
                
                response = raw_response.parse()
                response_params = self._response_to_params(response)
                
                messages.append({
                    "role": "assistant",
                    "content": response_params,
                })
                
                tool_result_content = []
                for content_block in response_params:
                    output_callback(content_block)
                    if content_block["type"] == "tool_use":
                        result = await self.tools.run(
                            name=content_block["name"],
                            tool_input=cast(Dict[str, Any], content_block["input"]),
                        )
                        tool_result_content.append(
                            self._make_api_tool_result(result, content_block["id"])
                        )
                        tool_output_callback(result, content_block["id"])
                
                if not tool_result_content:
                    return messages
                
                messages.append({"content": tool_result_content, "role": "user"})
                
            except (APIStatusError, APIResponseValidationError, APIError) as e:
                api_response_callback(e.request, getattr(e, 'response', None), e)
                return messages
    
    def _response_to_params(
        self, response: BetaMessage
    ) -> List[Union[BetaTextBlockParam, BetaToolUseBlockParam]]:
        """Convert API response to parameters."""
        res = []
        for block in response.content:
            if isinstance(block, BetaTextBlock):
                res.append({"type": "text", "text": block.text})
            else:
                res.append(cast(BetaToolUseBlockParam, block.model_dump()))
        return res
    
    def _make_api_tool_result(
        self, result: ToolResult, tool_use_id: str
    ) -> BetaToolResultBlockParam:
        """Convert a ToolResult to an API ToolResultBlockParam."""
        tool_result_content = []
        is_error = False
        
        if result.error:
            is_error = True
            error_text = result.error
            if result.system:
                error_text = f"<system>{result.system}</system>\n{error_text}"
            tool_result_content = error_text
        else:
            if result.output:
                output_text = result.output
                if result.system:
                    output_text = f"<system>{result.system}</system>\n{output_text}"
                tool_result_content.append({
                    "type": "text",
                    "text": output_text,
                })
            
            if result.base64_image:
                tool_result_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                })
        
        return {
            "type": "tool_result",
            "content": tool_result_content,
            "tool_use_id": tool_use_id,
            "is_error": is_error,
        }

# Sample usage
async def main():
    # Replace with your API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return
    
    api = ComputerUseAPI(api_key)
    
    def output_callback(content):
        if content["type"] == "text":
            print(f"Assistant: {content['text']}")
        elif content["type"] == "tool_use":
            print(f"Tool use: {content['name']}, Input: {content['input']}")
    
    def tool_output_callback(result, tool_id):
        if result.output:
            print(f"Tool output: {result.output}")
        if result.error:
            print(f"Tool error: {result.error}")
        if result.base64_image:
            print("Tool returned an image")
    
    def api_response_callback(request, response, error):
        if error:
            print(f"API error: {error}")
    
    user_input = input("What would you like to do? ")
    await api.run_conversation(
        user_input,
        output_callback,
        tool_output_callback,
        api_response_callback,
    )

if __name__ == "__main__":
    asyncio.run(main())
