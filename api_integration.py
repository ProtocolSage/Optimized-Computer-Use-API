#!/usr/bin/env python3
"""
API Integration Module for Claude Computer Use API

This module handles interactions with the Anthropic Claude API, managing:
- API authentication
- Message formatting
- Request/response handling
- Error management
- Rate limiting
"""

import os
import time
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, AsyncGenerator

import httpx
from anthropic import Anthropic
from anthropic.types import (
    MessageParam,
    ToolParam,
    ToolResultParam,
    ContentBlock,
    Tool,
    CompletionCreateParams
)
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('api_integration')

# Load environment variables
load_dotenv()

# Default constants
DEFAULT_MODEL = "claude-3-5-sonnet-20240620"
MAX_RETRIES = 3
RETRY_DELAY = 2
DEFAULT_TIMEOUT = 120


class ClaudeAPIClient:
    """
    Client for interacting with Claude Computer Use API
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = DEFAULT_MODEL,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize the Claude API client

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in completion
            temperature: Temperature for generation (0.0-1.0)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("No Anthropic API key provided. Set ANTHROPIC_API_KEY environment variable or pass api_key.")
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.client = Anthropic(api_key=self.api_key)
        self.system_prompt = self._get_default_system_prompt()
        
        # Define available tools
        self.available_tools = self._register_tools()
        
        logger.info(f"Initialized Claude API client with model: {model}")
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for Computer Use API"""
        return """You are Claude, an AI assistant with Computer Use capability. You can use tools to control the computer, 
        take screenshots, execute commands, and manipulate files safely. Remember to:
        
        1. Use the appropriate tool for each task
        2. Be precise with UI interactions
        3. Validate inputs and outputs
        4. Respect security boundaries
        5. Show your reasoning step-by-step
        6. Take screenshots to verify results when appropriate
        7. Be careful with commands that modify the system
        
        Execute tasks efficiently and explain your actions clearly."""
    
    def _register_tools(self) -> Dict[str, Tool]:
        """Register available tools for Computer Use API"""
        tools = [
            Tool(
                name="computer",
                description="Tool to control keyboard, mouse, and get screenshots",
                input_schema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["click", "type", "press", "move", "screenshot", "getWindowInfo"]
                        },
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "text": {"type": "string"},
                        "key": {"type": "string"},
                        "window_title": {"type": "string"}
                    },
                    "required": ["action"]
                }
            ),
            Tool(
                name="command",
                description="Execute system commands",
                input_schema={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"}
                    },
                    "required": ["command"]
                }
            ),
            Tool(
                name="file",
                description="Read, write, or delete files",
                input_schema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["read", "write", "append", "delete", "list"]
                        },
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["action", "path"]
                }
            )
        ]
        
        return {tool.name: tool for tool in tools}
    
    def set_system_prompt(self, system_prompt: str) -> None:
        """
        Set a custom system prompt
        
        Args:
            system_prompt: The system prompt to use
        """
        self.system_prompt = system_prompt
        logger.info("Updated system prompt")

    async def send_message(
        self, 
        messages: List[Dict[str, Any]],
        tool_results: Optional[List[ToolResultParam]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Claude API and get a response
        
        Args:
            messages: List of message objects
            tool_results: Optional tool execution results
            
        Returns:
            Claude API response
        """
        retries = 0
        
        formatted_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Format content appropriately based on type
            if isinstance(content, str):
                formatted_content = content
            elif isinstance(content, list):
                formatted_content = content
            else:
                formatted_content = str(content)
            
            formatted_messages.append(MessageParam(
                role=role,
                content=formatted_content
            ))
        
        # Set up request parameters
        params = CompletionCreateParams(
            model=self.model,
            messages=formatted_messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.system_prompt,
            tools=list(self.available_tools.values())
        )
        
        # Add tool results if provided
        if tool_results:
            params["tool_results"] = tool_results
            
        while retries < MAX_RETRIES:
            try:
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    **params
                )
                logger.debug(f"API response: {response}")
                return response
            except Exception as e:
                retries += 1
                logger.error(f"API request failed (attempt {retries}/{MAX_RETRIES}): {str(e)}")
                if retries >= MAX_RETRIES:
                    raise
                await asyncio.sleep(RETRY_DELAY * retries)
    
    async def execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call from Claude
        
        Args:
            tool_call: Tool call details from Claude's response
            
        Returns:
            Tool execution results
        """
        tool_name = tool_call.get("name")
        tool_input = tool_call.get("input", {})
        
        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
        
        # This is just a placeholder - actual tool execution happens in computer_use_api.py
        # This method will be used by other classes to register callbacks for tool execution
        return {"result": f"Tool {tool_name} executed with input {tool_input}", "status": "success"}
    
    def format_tool_result(self, tool_call_id: str, result: Dict[str, Any]) -> ToolResultParam:
        """
        Format tool execution results for Claude API
        
        Args:
            tool_call_id: ID of the tool call
            result: Results from tool execution
            
        Returns:
            Formatted tool result
        """
        return ToolResultParam(
            tool_call_id=tool_call_id,
            output=json.dumps(result)
        )


class StreamingAPIClient(ClaudeAPIClient):
    """
    Extended Claude API client with streaming support
    """
    
    async def stream_message(
        self, 
        messages: List[Dict[str, Any]],
        tool_results: Optional[List[ToolResultParam]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a message from Claude API
        
        Args:
            messages: List of message objects
            tool_results: Optional tool execution results
            
        Yields:
            Chunks of Claude API response
        """
        formatted_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Format content appropriately based on type
            if isinstance(content, str):
                formatted_content = content
            elif isinstance(content, list):
                formatted_content = content
            else:
                formatted_content = str(content)
            
            formatted_messages.append(MessageParam(
                role=role,
                content=formatted_content
            ))
        
        # Set up request parameters
        params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": self.system_prompt,
            "tools": list(self.available_tools.values()),
            "stream": True
        }
        
        # Add tool results if provided
        if tool_results:
            params["tool_results"] = tool_results
        
        try:
            with self.client.messages.stream(**params) as stream:
                for chunk in stream:
                    if chunk.type == "content_block_delta":
                        yield {"type": "text", "content": chunk.delta.text}
                    elif chunk.type == "tool_use":
                        yield {"type": "tool_call", "tool_call": chunk.tool_use}
                    elif chunk.type == "message_stop":
                        yield {"type": "end"}
        except Exception as e:
            logger.error(f"Streaming API request failed: {str(e)}")
            raise


# Utility functions
async def check_api_status(api_key: Optional[str] = None) -> Tuple[bool, str]:
    """
    Check if the Anthropic API is operational
    
    Args:
        api_key: Optional API key to use
        
    Returns:
        (status, message) tuple
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return False, "No API key provided"
    
    try:
        client = httpx.AsyncClient(timeout=10.0)
        headers = {
            "x-api-key": api_key,
            "content-type": "application/json",
        }
        
        # Make a minimal API request just to test connectivity
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json={
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        
        await client.aclose()
        
        if response.status_code == 200:
            return True, "API is operational"
        else:
            return False, f"API returned status code {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"API check failed: {str(e)}"