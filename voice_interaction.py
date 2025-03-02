#!/usr/bin/env python3
"""
Voice Interaction Module for Claude Computer Use API

This module provides automatic voice interaction capabilities:
- Speech to text (input) using OpenAI's Whisper model
- Text to speech (output) for Claude's responses

Can be used standalone or integrated with the GUI wrapper.
"""

import os
import sys
import time
import json
import asyncio
import logging
import threading
import argparse
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/voice_interaction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('voice_interaction')

# Add the current directory to path for extension imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import optional dependencies
try:
    from extension_module import ExtensionManager
    from api_integration import ClaudeAPIClient
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    logger.warning("Core dependencies missing. This module must be run from the main project directory.")

# Configuration
DEFAULT_CONFIG = {
    "auto_listen": True,
    "auto_speak": True,
    "speech_recognition": {
        "model_size": "base",  # tiny, base, small, medium, large
        "timeout": 30,
        "save_audio": True
    },
    "text_to_speech": {
        "rate": 180,  # Speed (words per minute)
        "volume": 1.0,  # Volume (0.0 to 1.0)
        "voice_index": 0  # Voice to use
    },
    "wake_words": [
        "hey claude",
        "okay claude",
        "claude",
        "computer"
    ],
    "activation_commands": [
        "listen",
        "wake up",
        "can you hear me"
    ],
    "deactivation_commands": [
        "stop listening",
        "go to sleep",
        "stop voice"
    ]
}

class VoiceInteraction:
    """
    Handles voice-based interaction with Claude
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize voice interaction
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = DEFAULT_CONFIG
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Update default config with loaded values
                    self._update_config(loaded_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {str(e)}")
        
        # Initialize state
        self.active = False
        self.listening_thread = None
        self.extension_manager = None
        self.speech_recognition = None
        self.text_to_speech = None
        self.api_client = None
        self.message_handler = None
        
        # Initialize extensions if dependencies are available
        if DEPENDENCIES_AVAILABLE:
            self._initialize_extensions()
        else:
            logger.error("Could not initialize extensions due to missing dependencies")
    
    def _update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        for key, value in new_config.items():
            if key in self.config:
                if isinstance(value, dict) and isinstance(self.config[key], dict):
                    self._update_config_section(self.config[key], value)
                else:
                    self.config[key] = value
            else:
                self.config[key] = value
    
    def _update_config_section(self, section: Dict[str, Any], new_section: Dict[str, Any]) -> None:
        """Update a section of the configuration"""
        for key, value in new_section.items():
            if key in section:
                if isinstance(value, dict) and isinstance(section[key], dict):
                    self._update_config_section(section[key], value)
                else:
                    section[key] = value
            else:
                section[key] = value
    
    def _initialize_extensions(self) -> None:
        """Initialize required extensions"""
        try:
            # Initialize extension manager
            self.extension_manager = ExtensionManager()
            
            # Add extension directories
            for directory in ['extensions', 'custom_extensions']:
                self.extension_manager.registry.add_extension_dir(directory)
            
            # Discover extensions
            self.extension_manager.registry.discover_extensions()
            
            # Get speech recognition extension
            self.speech_recognition = self.extension_manager.registry.get_extension("speech_recognition")
            if not self.speech_recognition:
                logger.warning("Speech recognition extension not found")
            
            # Get text-to-speech extension
            self.text_to_speech = self.extension_manager.registry.get_extension("text_to_speech")
            if not self.text_to_speech:
                logger.warning("Text-to-speech extension not found")
            
            # Initialize API client if needed for direct integration
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.api_client = ClaudeAPIClient(api_key=api_key)
            
            logger.info("Extensions initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing extensions: {str(e)}")
    
    def set_message_handler(self, handler: Callable[[str], None]) -> None:
        """
        Set a callback for handling recognized speech
        
        Args:
            handler: Function to call with recognized text
        """
        self.message_handler = handler
        logger.info("Message handler set")
    
    async def speak(self, text: str) -> None:
        """
        Convert text to speech
        
        Args:
            text: Text to speak
        """
        if not self.text_to_speech:
            logger.warning("Text-to-speech extension not available")
            return
        
        try:
            # Configure TTS settings from config
            tts_config = self.config.get("text_to_speech", {})
            rate = tts_config.get("rate", 180)
            volume = tts_config.get("volume", 1.0)
            voice_index = tts_config.get("voice_index", 0)
            
            # Execute TTS
            result = await self.extension_manager.execute_extension(
                "text_to_speech", 
                "speak",
                text=text,
                rate=rate,
                volume=volume,
                voice_index=voice_index
            )
            
            if not result or result.get("status") != "success":
                logger.error(f"TTS error: {result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error in speak: {str(e)}")
    
    async def listen_once(self) -> Optional[str]:
        """
        Listen for speech once and convert to text
        
        Returns:
            Recognized text or None if no speech detected
        """
        if not self.speech_recognition:
            logger.warning("Speech recognition extension not available")
            return None
        
        try:
            # Configure speech recognition settings from config
            sr_config = self.config.get("speech_recognition", {})
            timeout = sr_config.get("timeout", 30)
            save_audio = sr_config.get("save_audio", True)
            
            # Execute speech recognition
            result = await self.extension_manager.execute_extension(
                "speech_recognition", 
                "listen",
                timeout=timeout,
                save_audio=save_audio
            )
            
            if not result or result.get("status") != "success":
                error_msg = result.get("message", "Unknown error") if result else "No result"
                logger.error(f"Speech recognition error: {error_msg}")
                return None
            
            text = result.get("text", "").strip()
            logger.info(f"Recognized speech: {text}")
            return text
        except Exception as e:
            logger.error(f"Error in listen_once: {str(e)}")
            return None
    
    async def _process_speech(self, text: str) -> None:
        """
        Process recognized speech
        
        Args:
            text: Recognized text
        """
        if not text:
            return
        
        # Convert to lowercase for easier comparison
        text_lower = text.lower()
        
        # Check for deactivation commands
        for command in self.config.get("deactivation_commands", []):
            if command in text_lower:
                logger.info("Deactivation command detected")
                await self.speak("Voice interaction deactivated")
                self.active = False
                return
        
        # If we have a message handler, call it
        if self.message_handler:
            self.message_handler(text)
        else:
            logger.warning("No message handler set, ignored speech input")
    
    async def _continuous_listening(self) -> None:
        """Background task for continuous listening"""
        logger.info("Starting continuous listening")
        
        try:
            # Configure speech recognition model
            sr_config = self.config.get("speech_recognition", {})
            model_size = sr_config.get("model_size", "base")
            
            # Set the model size if different from default
            await self.extension_manager.execute_extension(
                "speech_recognition", 
                "set_model",
                model_size=model_size
            )
            
            # Announce that we're listening
            await self.speak("Voice interaction activated")
            
            # Main listening loop
            while self.active:
                speech_text = await self.listen_once()
                if speech_text:
                    await self._process_speech(speech_text)
                
                # Short delay to prevent CPU hogging
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in continuous listening: {str(e)}")
        finally:
            logger.info("Continuous listening stopped")
    
    def start_listening(self) -> None:
        """Start continuous listening in a background thread"""
        if self.active:
            logger.warning("Already listening")
            return
        
        if not self.speech_recognition:
            logger.error("Speech recognition extension not available")
            return
        
        self.active = True
        
        # Create a new asyncio event loop for the background thread
        def run_listening_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._continuous_listening())
            loop.close()
        
        # Start the background thread
        self.listening_thread = threading.Thread(target=run_listening_loop)
        self.listening_thread.daemon = True
        self.listening_thread.start()
        logger.info("Started listening thread")
    
    def stop_listening(self) -> None:
        """Stop continuous listening"""
        self.active = False
        logger.info("Stopping listening thread")
    
    def is_listening(self) -> bool:
        """Check if continuous listening is active"""
        return self.active
    
    async def process_response(self, response_text: str) -> None:
        """
        Process a response from Claude, speaking it if enabled
        
        Args:
            response_text: Text from Claude
        """
        if self.config.get("auto_speak", True) and self.text_to_speech:
            await self.speak(response_text)


async def main():
    """Main function for standalone operation"""
    parser = argparse.ArgumentParser(description="Voice Interaction for Claude Computer Use API")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--no-listen", action="store_true", help="Don't automatically start listening")
    args = parser.parse_args()
    
    # Initialize voice interaction
    voice = VoiceInteraction(config_path=args.config)
    
    # Define message handler
    async def handle_message(text):
        print(f"Recognized: {text}")
        # Here you would integrate with Claude API to get a response
        # For this example, we'll just echo back
        response = f"I heard: {text}"
        await voice.speak(response)
    
    # Set the message handler
    voice.set_message_handler(lambda text: asyncio.create_task(handle_message(text)))
    
    # Start listening if auto-listen is enabled
    if voice.config.get("auto_listen", True) and not args.no_listen:
        voice.start_listening()
    
    try:
        # Keep the main thread running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping voice interaction...")
    finally:
        voice.stop_listening()


if __name__ == "__main__":
    asyncio.run(main())