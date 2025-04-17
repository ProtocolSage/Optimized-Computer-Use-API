#!/usr/bin/env python3
"""
Text-to-Speech Extension for Claude Computer Use API

This extension provides text-to-speech functionality, allowing Claude to 
convert text to speech for voice feedback using local TTS engines.
"""

import os
import json
import asyncio
import logging
import tempfile
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

import pyttsx3

# Import the extension base class from the parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension_module import Extension

# Configure logging
logger = logging.getLogger('text_to_speech')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler('logs/text_to_speech.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Constants
OUTPUT_DIR = Path('outputs/text_to_speech')


class TextToSpeech(Extension):
    """
    Extension for converting text to speech
    """
    
    name = "text_to_speech"
    description = "Converts text to speech for voice feedback"
    version = "1.0.0"
    author = "Claude Computer Use API Team"
    
    def __init__(self):
        """Initialize the Text-to-Speech extension"""
        super().__init__()
        
        # Initialize TTS engine
        try:
            self.engine = pyttsx3.init()
            self.voices = self.engine.getProperty('voices')
            
            # Set default properties
            self.engine.setProperty('rate', 180)  # Speed (words per minute)
            self.engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
            
            # Set default voice (first voice in the system)
            if self.voices:
                self.engine.setProperty('voice', self.voices[0].id)
            
            self.available = True
            self.current_voice_index = 0
            
            # Ensure output directory exists
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            
            logger.info(f"Text-to-Speech extension initialized with {len(self.voices)} voices")
        
        except Exception as e:
            logger.error(f"Failed to initialize Text-to-Speech engine: {str(e)}")
            self.available = False
            self.engine = None
            self.voices = []
    
    async def speak(self, 
                  text: str, 
                  rate: Optional[int] = None, 
                  volume: Optional[float] = None,
                  voice_index: Optional[int] = None,
                  wait: bool = True) -> Dict[str, Any]:
        """
        Convert text to speech and speak it
        
        Args:
            text: Text to convert to speech
            rate: Speech rate (words per minute)
            volume: Volume (0.0 to 1.0)
            voice_index: Index of the voice to use
            wait: Whether to wait for speech to complete
            
        Returns:
            Status information
        """
        if not self.available or not self.engine:
            return {
                "status": "error",
                "message": "Text-to-Speech engine is not available"
            }
        
        try:
            # Apply custom settings if provided
            if rate is not None:
                self.engine.setProperty('rate', max(50, min(400, rate)))
            
            if volume is not None:
                self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
            
            if voice_index is not None and 0 <= voice_index < len(self.voices):
                self.engine.setProperty('voice', self.voices[voice_index].id)
                self.current_voice_index = voice_index
            
            # Use asyncio to run the speech in a separate thread
            loop = asyncio.get_event_loop()
            
            if wait:
                # Run synchronously if wait is True
                await loop.run_in_executor(None, lambda: self.engine.say(text))
                await loop.run_in_executor(None, self.engine.runAndWait)
            else:
                # Start in background if wait is False
                asyncio.create_task(self._speak_async(text))
            
            return {
                "status": "success",
                "message": "Text spoken successfully" if wait else "Text speech started",
                "text": text,
                "settings": {
                    "rate": self.engine.getProperty('rate'),
                    "volume": self.engine.getProperty('volume'),
                    "voice": self.current_voice_index
                }
            }
        
        except Exception as e:
            logger.error(f"Speech error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to speak text: {str(e)}"
            }
    
    async def _speak_async(self, text: str) -> None:
        """
        Background task for non-blocking speech
        
        Args:
            text: Text to speak
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.engine.say(text))
        await loop.run_in_executor(None, self.engine.runAndWait)
    
    async def save(self, 
                 text: str, 
                 filename: Optional[str] = None,
                 rate: Optional[int] = None, 
                 volume: Optional[float] = None,
                 voice_index: Optional[int] = None) -> Dict[str, Any]:
        """
        Convert text to speech and save to a file
        
        Args:
            text: Text to convert to speech
            filename: Name of the output file (without extension)
            rate: Speech rate (words per minute)
            volume: Volume (0.0 to 1.0)
            voice_index: Index of the voice to use
            
        Returns:
            Status information
        """
        if not self.available or not self.engine:
            return {
                "status": "error",
                "message": "Text-to-Speech engine is not available"
            }
        
        try:
            # Apply custom settings if provided
            if rate is not None:
                self.engine.setProperty('rate', max(50, min(400, rate)))
            
            if volume is not None:
                self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
            
            if voice_index is not None and 0 <= voice_index < len(self.voices):
                self.engine.setProperty('voice', self.voices[voice_index].id)
                self.current_voice_index = voice_index
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tts_{timestamp}"
            
            # Ensure the filename has no extension and is safe
            filename = os.path.splitext(os.path.basename(filename))[0]
            filename = "".join(c for c in filename if c.isalnum() or c in "_-")
            
            # Create full output path
            output_path = OUTPUT_DIR / f"{filename}.mp3"
            
            # Save to file using a temporary file first
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Use asyncio to run the save operation in a separate thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self.engine.save_to_file(text, temp_path)
            )
            await loop.run_in_executor(None, self.engine.runAndWait)
            
            # Copy from temp location to final destination
            import shutil
            shutil.move(temp_path, output_path)
            
            return {
                "status": "success",
                "message": f"Text saved to {output_path}",
                "file_path": str(output_path),
                "text": text,
                "settings": {
                    "rate": self.engine.getProperty('rate'),
                    "volume": self.engine.getProperty('volume'),
                    "voice": self.current_voice_index
                }
            }
        
        except Exception as e:
            logger.error(f"Save error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to save speech: {str(e)}"
            }
    
    async def get_voices(self) -> Dict[str, Any]:
        """
        Get available voices
        
        Returns:
            List of available voices
        """
        if not self.available or not self.engine:
            return {
                "status": "error",
                "message": "Text-to-Speech engine is not available"
            }
        
        voice_list = []
        for i, voice in enumerate(self.voices):
            voice_list.append({
                "index": i,
                "id": voice.id,
                "name": voice.name,
                "languages": getattr(voice, 'languages', []),
                "gender": getattr(voice, 'gender', None),
                "age": getattr(voice, 'age', None),
                "current": i == self.current_voice_index
            })
        
        return {
            "status": "success",
            "voices": voice_list,
            "current_voice": self.current_voice_index,
            "count": len(voice_list)
        }
    
    async def execute(self, command: str = "speak", **kwargs) -> Dict[str, Any]:
        """
        Execute extension commands
        
        Args:
            command: The command to execute
            **kwargs: Command-specific arguments
            
        Returns:
            Command execution results
        """
        if command == "speak":
            return await self.speak(
                text=kwargs.get("text", ""),
                rate=kwargs.get("rate"),
                volume=kwargs.get("volume"),
                voice_index=kwargs.get("voice"),
                wait=kwargs.get("wait", True)
            )
        elif command == "save":
            return await self.save(
                text=kwargs.get("text", ""),
                filename=kwargs.get("filename"),
                rate=kwargs.get("rate"),
                volume=kwargs.get("volume"),
                voice_index=kwargs.get("voice")
            )
        elif command == "voices":
            return await self.get_voices()
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}


# Add this extension to the registry
if __name__ == "__main__":
    # This allows for testing the extension directly
    extension = TextToSpeech()
    print(f"Initialized {extension.name} v{extension.version}")
    print(f"Commands: speak, save, voices")