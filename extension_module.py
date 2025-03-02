"""
Extensions Module for the Computer Use API.
Provides additional capabilities through a plugin architecture.
"""

import os
import importlib.util
import inspect
import pkgutil
import sys
import logging
from typing import Dict, List, Any, Callable, Optional, Type, Tuple, Union
from abc import ABC, abstractmethod
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("extensions.log"), logging.StreamHandler()]
)
logger = logging.getLogger("extensions")

# Base Extension class
class Extension(ABC):
    """Base class for all extensions."""
    
    name: str = "unnamed_extension"
    description: str = "No description provided"
    version: str = "0.1.0"
    author: str = "Unknown"
    
    def __init__(self):
        self.enabled = True
        self.config = {}
        logger.info(f"Initialized extension: {self.name} v{self.version}")
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the extension's functionality."""
        pass
    
    def load_config(self, config: Dict[str, Any]) -> None:
        """Load configuration for the extension."""
        self.config = config
        logger.info(f"Loaded configuration for {self.name}")
    
    def enable(self) -> None:
        """Enable the extension."""
        self.enabled = True
        logger.info(f"Enabled extension: {self.name}")
    
    def disable(self) -> None:
        """Disable the extension."""
        self.enabled = False
        logger.info(f"Disabled extension: {self.name}")
    
    @property
    def status(self) -> Dict[str, Any]:
        """Get the status of the extension."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "enabled": self.enabled,
            "config": self.config
        }

# Extension Registry
class ExtensionRegistry:
    """Registry for managing extensions."""
    
    def __init__(self):
        self.extensions: Dict[str, Extension] = {}
        self.extension_dirs: List[str] = ["extensions"]
        logger.info("Initialized ExtensionRegistry")
    
    def register(self, extension: Extension) -> None:
        """Register an extension."""
        if extension.name in self.extensions:
            logger.warning(f"Extension {extension.name} already registered. Overwriting.")
        
        self.extensions[extension.name] = extension
        logger.info(f"Registered extension: {extension.name}")
    
    def unregister(self, extension_name: str) -> None:
        """Unregister an extension."""
        if extension_name in self.extensions:
            del self.extensions[extension_name]
            logger.info(f"Unregistered extension: {extension_name}")
        else:
            logger.warning(f"Extension {extension_name} not found. Cannot unregister.")
    
    def get_extension(self, extension_name: str) -> Optional[Extension]:
        """Get an extension by name."""
        return self.extensions.get(extension_name)
    
    def list_extensions(self) -> List[Dict[str, Any]]:
        """List all registered extensions."""
        return [ext.status for ext in self.extensions.values()]
    
    def add_extension_dir(self, directory: str) -> None:
        """Add a directory to search for extensions."""
        if os.path.isdir(directory) and directory not in self.extension_dirs:
            self.extension_dirs.append(directory)
            logger.info(f"Added extension directory: {directory}")
        else:
            logger.warning(f"Directory {directory} is not valid or already added.")
    
    def discover_extensions(self) -> None:
        """Discover and register extensions from all extension directories."""
        for directory in self.extension_dirs:
            if not os.path.isdir(directory):
                logger.warning(f"Directory {directory} not found. Skipping.")
                continue
            
            logger.info(f"Discovering extensions in {directory}")
            self._discover_in_directory(directory)
    
    def _discover_in_directory(self, directory: str) -> None:
        """Discover extensions in a specific directory."""
        if directory not in sys.path:
            sys.path.insert(0, directory)
        
        for _, name, is_pkg in pkgutil.iter_modules([directory]):
            if not is_pkg:
                try:
                    module_path = os.path.join(directory, f"{name}.py")
                    spec = importlib.util.spec_from_file_location(name, module_path)
                    if spec is None or spec.loader is None:
                        logger.warning(f"Failed to load spec for {module_path}")
                        continue
                        
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    for item_name, item in inspect.getmembers(module):
                        if (inspect.isclass(item) and 
                            issubclass(item, Extension) and 
                            item is not Extension):
                            try:
                                extension = item()
                                self.register(extension)
                            except Exception as e:
                                logger.error(f"Error instantiating extension {item_name}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error loading module {name}: {str(e)}")

# Extension Manager
class ExtensionManager:
    """Manager for handling extension operations."""
    
    def __init__(self):
        self.registry = ExtensionRegistry()
        logger.info("Initialized ExtensionManager")
    
    def initialize(self, config_file: Optional[str] = None) -> None:
        """Initialize the extension manager."""
        # Load configurations
        if config_file and os.path.isfile(config_file):
            self._load_config(config_file)
        
        # Discover extensions
        self.registry.discover_extensions()
        logger.info(f"Discovered {len(self.registry.extensions)} extensions")
    
    def _load_config(self, config_file: str) -> None:
        """Load configuration from file."""
        import json
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Add extension directories
            for directory in config.get('extension_dirs', []):
                self.registry.add_extension_dir(directory)
            
            # Load extension configs
            for ext_name, ext_config in config.get('extensions', {}).items():
                extension = self.registry.get_extension(ext_name)
                if extension:
                    extension.load_config(ext_config)
                    
                    # Enable/disable based on config
                    if ext_config.get('enabled', True):
                        extension.enable()
                    else:
                        extension.disable()
                        
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {str(e)}")
    
    async def execute_extension(self, extension_name: str, *args, **kwargs) -> Any:
        """Execute an extension by name."""
        extension = self.registry.get_extension(extension_name)
        if not extension:
            logger.warning(f"Extension {extension_name} not found")
            return None
        
        if not extension.enabled:
            logger.warning(f"Extension {extension_name} is disabled")
            return None
        
        try:
            logger.info(f"Executing extension {extension_name}")
            result = await extension.execute(*args, **kwargs)
            logger.info(f"Extension {extension_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing extension {extension_name}: {str(e)}")
            return None
    
    def list_extensions(self) -> List[Dict[str, Any]]:
        """List all registered extensions."""
        return self.registry.list_extensions()
    
    def enable_extension(self, extension_name: str) -> bool:
        """Enable an extension."""
        extension = self.registry.get_extension(extension_name)
        if extension:
            extension.enable()
            return True
        return False
    
    def disable_extension(self, extension_name: str) -> bool:
        """Disable an extension."""
        extension = self.registry.get_extension(extension_name)
        if extension:
            extension.disable()
            return True
        return False

# Sample extensions

class WebSearchExtension(Extension):
    """Extension for web searching capabilities."""
    
    name = "web_search"
    description = "Provides web search functionality"
    version = "1.0.0"
    author = "Claude API Team"
    
    def __init__(self):
        super().__init__()
        # Import required libraries here to avoid dependencies for other extensions
        try:
            import requests
            self.requests = requests
            self._has_dependencies = True
        except ImportError:
            logger.warning("WebSearchExtension requires 'requests' package. Install using: pip install requests")
            self._has_dependencies = False
    
    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Execute a web search query."""
        if not self._has_dependencies:
            return {"error": "Missing dependencies. Install requests package."}
        
        try:
            # Using a simple Duck Duck Go search API
            url = f"https://api.duckduckgo.com/?q={query}&format=json"
            response = self.requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if 'RelatedTopics' in data:
                for topic in data['RelatedTopics'][:max_results]:
                    if 'Text' in topic:
                        results.append({
                            'title': topic.get('Text', '').split(' - ')[0],
                            'description': topic.get('Text', ''),
                            'url': topic.get('FirstURL', '')
                        })
            
            return {
                "query": query,
                "results": results,
                "success": True
            }
        except Exception as e:
            logger.error(f"Error in web search: {str(e)}")
            return {
                "query": query,
                "results": [],
                "success": False,
                "error": str(e)
            }

class NotificationExtension(Extension):
    """Extension for sending notifications."""
    
    name = "notification"
    description = "Enables sending desktop notifications"
    version = "1.0.0"
    author = "Claude API Team"
    
    def __init__(self):
        super().__init__()
        try:
            # For Windows
            from win10toast import ToastNotifier
            self.notifier = ToastNotifier()
            self._has_dependencies = True
            self._platform = "windows"
        except ImportError:
            try:
                # For Linux/MacOS
                import notify2
                notify2.init("Claude Computer Use API")
                self.notifier = notify2
                self._has_dependencies = True
                self._platform = "linux"
            except ImportError:
                logger.warning("NotificationExtension requires notification packages.")
                logger.warning("For Windows: pip install win10toast")
                logger.warning("For Linux: pip install notify2")
                self._has_dependencies = False
                self._platform = "unknown"
    
    async def execute(self, title: str, message: str, duration: int = 5) -> Dict[str, bool]:
        """Send a desktop notification."""
        if not self._has_dependencies:
            return {"success": False, "error": "Missing dependencies."}
        
        try:
            if self._platform == "windows":
                self.notifier.show_toast(
                    title,
                    message,
                    duration=duration,
                    threaded=True
                )
            elif self._platform == "linux":
                notification = self.notifier.Notification(title, message)
                notification.show()
            
            return {"success": True}
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return {"success": False, "error": str(e)}

class TextToSpeechExtension(Extension):
    """Extension for text-to-speech capabilities."""
    
    name = "text_to_speech"
    description = "Converts text to speech"
    version = "1.0.0"
    author = "Claude API Team"
    
    def __init__(self):
        super().__init__()
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self._has_dependencies = True
        except ImportError:
            logger.warning("TextToSpeechExtension requires 'pyttsx3' package. Install using: pip install pyttsx3")
            self._has_dependencies = False
    
    async def execute(self, text: str, rate: int = 150, volume: float = 1.0) -> Dict[str, bool]:
        """Convert text to speech."""
        if not self._has_dependencies:
            return {"success": False, "error": "Missing dependencies. Install pyttsx3 package."}
        
        try:
            # Configure the engine
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            # Use asyncio to run the speech in a separate thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._speak, text)
            
            return {"success": True}
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _speak(self, text: str) -> None:
        """Speak the given text."""
        self.engine.say(text)
        self.engine.runAndWait()

# Extension usage example
async def extension_example():
    """Example of using extensions."""
    manager = ExtensionManager()
    
    # Add a custom extension directory
    manager.registry.add_extension_dir("custom_extensions")
    
    # Initialize extensions
    manager.initialize()
    
    # List available extensions
    print("Available Extensions:")
    for ext in manager.list_extensions():
        print(f"- {ext['name']} (v{ext['version']}): {ext['description']}")
        print(f"  Enabled: {ext['enabled']}")
    
    # Execute a text-to-speech extension
    result = await manager.execute_extension("text_to_speech", "Hello, this is Claude speaking!")
    print(f"TTS Result: {result}")
    
    # Execute a web search extension
    search_result = await manager.execute_extension("web_search", "Claude AI capabilities")
    if search_result and search_result.get("success"):
        print(f"Found {len(search_result['results'])} results for '{search_result['query']}'")
        for i, result in enumerate(search_result['results'], 1):
            print(f"{i}. {result['title']}")
            print(f"   {result['description']}")
            print(f"   URL: {result['url']}")

if __name__ == "__main__":
    # Run the example if this file is executed directly
    asyncio.run(extension_example())
