"""
Voice configuration module for loading and saving voice-related settings.
Provides Pydantic models for type validation and serialization.
"""

from pathlib import Path
from typing import Optional
import json
import logging

from pydantic import BaseModel, Field

# Set up logging
logger = logging.getLogger(__name__)

class SpeechRecognitionConfig(BaseModel):
    """Configuration settings for speech recognition."""
    model_size: str = Field(description="Size of the speech recognition model (tiny, base, small, medium, large)")
    timeout: int = Field(description="Timeout in seconds for speech recognition")
    save_audio: bool = Field(description="Whether to save audio recordings")

class TextToSpeechConfig(BaseModel):
    """Configuration settings for text-to-speech."""
    rate: int = Field(description="Speech rate in words per minute")
    volume: float = Field(description="Volume level from 0.0 to 1.0") 
    voice_index: int = Field(description="Index of the voice to use")

class VoiceConfig(BaseModel):
    """Configuration for voice interaction components."""
    auto_listen: bool = Field(description="Whether to automatically listen for commands")
    auto_speak: bool = Field(description="Whether to automatically speak responses")
    speech_recognition: SpeechRecognitionConfig
    text_to_speech: TextToSpeechConfig
    wake_words: list[str] = Field(description="Words that trigger the assistant to start listening")
    activation_commands: list[str] = Field(description="Commands that activate voice mode")
    deactivation_commands: list[str] = Field(description="Commands that deactivate voice mode")

def load_voice_config(path: str = "config/voice_config.json") -> Optional[VoiceConfig]:
    """
    Load voice configuration from the specified JSON file.
    
    Args:
        path: Relative path to the config file from the project root
        
    Returns:
        VoiceConfig object if successful, None if file not found or invalid
        
    Raises:
        ValueError: If the config file contains invalid data
    """
    try:
        # Get the project root directory (2 levels up from this file)
        config_path = Path(__file__).parent.parent / path
        
        # Make sure the file exists
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return None
            
        # Load and parse the JSON file
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            
        # Create and validate the config object
        return VoiceConfig(**config_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse config file {path}: {e}")
        raise ValueError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        logger.error(f"Error loading voice config: {e}")
        return None

def save_voice_config(config: VoiceConfig, path: str = "config/voice_config.json") -> bool:
    """
    Save voice configuration to the specified JSON file.
    
    Args:
        config: VoiceConfig object to save
        path: Relative path to save the config file from the project root
        
    Returns:
        True if successful, False otherwise
    """
    try:
        config_path = Path(__file__).parent.parent / path
        
        # Create parent directories if they don't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the config to the file
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(), f, indent=2)
        
        logger.info(f"Voice config saved to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save voice config: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Load the configuration
    config = load_voice_config()
    if config:
        print(f"Loaded config with {len(config.wake_words)} wake words")
        print(f"Voice rate: {config.text_to_speech.rate}")
    else:
        print("Failed to load configuration")
