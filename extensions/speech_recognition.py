#!/usr/bin/env python3
"""
Speech Recognition Extension for Claude Computer Use API

This extension provides speech-to-text capabilities using OpenAI's Whisper model,
allowing users to speak commands to Claude instead of typing.
"""

import os
import json
import asyncio
import logging
import tempfile
import time
import wave
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime

# Import the extension base class from the parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension_module import Extension

# Configure logging
logger = logging.getLogger('speech_recognition')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler('logs/speech_recognition.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Try importing optional dependencies
try:
    import pyaudio
    import numpy as np
    
    # Try to import OpenAI's Whisper first
    try:
        import whisper
        USING_OPENAI_WHISPER = True
        USING_FASTER_WHISPER = False
        logger.info("Using OpenAI Whisper for speech recognition")
    except ImportError:
        # If OpenAI's Whisper isn't available, try faster-whisper
        try:
            from faster_whisper import WhisperModel
            USING_OPENAI_WHISPER = False
            USING_FASTER_WHISPER = True
            logger.info("Using faster-whisper for speech recognition")
        except ImportError:
            USING_OPENAI_WHISPER = False
            USING_FASTER_WHISPER = False
            logger.warning("Neither whisper nor faster-whisper is available")
            
    DEPENDENCIES_AVAILABLE = USING_OPENAI_WHISPER or USING_FASTER_WHISPER
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    USING_OPENAI_WHISPER = False
    USING_FASTER_WHISPER = False
    logger.warning("Some dependencies are missing. Install using: pip install pyaudio numpy openai-whisper (or pip install pyaudio numpy faster-whisper)")

# Constants
AUDIO_DIR = Path('data/speech_recognition')
FORMAT = pyaudio.paInt16 if DEPENDENCIES_AVAILABLE else None
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 2  # seconds of silence to end recording
MIN_AUDIO_LENGTH = 1.0  # minimum audio length in seconds


class SpeechRecognition(Extension):
    """
    Extension for speech recognition using Whisper models (OpenAI or faster-whisper)
    """
    
    name = "speech_recognition"
    description = "Converts speech to text using Whisper models (OpenAI or faster-whisper)"
    version = "1.1.0"
    author = "Claude Computer Use API Team"
    
    def __init__(self):
        """Initialize the Speech Recognition extension"""
        super().__init__()
        
        # Set up directories
        os.makedirs(AUDIO_DIR, exist_ok=True)
        
        # Initialize components if dependencies are available
        if DEPENDENCIES_AVAILABLE:
            try:
                # Initialize audio interface
                self.audio = pyaudio.PyAudio()
                
                # Load the model (base model is ~74M parameters)
                self.model_size = "base"  # options: tiny, base, small, medium, large
                
                if USING_OPENAI_WHISPER:
                    # Load OpenAI Whisper model
                    logger.info(f"Loading OpenAI Whisper {self.model_size} model...")
                    self.model = whisper.load_model(self.model_size)
                    logger.info(f"OpenAI Whisper {self.model_size} model loaded")
                elif USING_FASTER_WHISPER:
                    # Load faster-whisper model
                    logger.info(f"Loading faster-whisper {self.model_size} model...")
                    # faster-whisper uses compute type for performance (fp16 is faster with GPU)
                    self.model = WhisperModel(self.model_size, device="auto", compute_type="int8")
                    logger.info(f"faster-whisper {self.model_size} model loaded")
                
                self.available = True
                logger.info("Speech Recognition extension initialized")
            except Exception as e:
                self.available = False
                logger.error(f"Failed to initialize Speech Recognition: {str(e)}")
        else:
            self.available = False
            logger.warning("Speech Recognition extension disabled due to missing dependencies")
    
    def __del__(self):
        """Clean up resources when the extension is destroyed"""
        if hasattr(self, 'audio') and self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {str(e)}")
    
    async def listen(self, 
                    timeout: Optional[int] = 30,
                    save_audio: bool = True) -> Dict[str, Any]:
        """
        Listen for speech and convert to text
        
        Args:
            timeout: Maximum recording time in seconds
            save_audio: Whether to save the audio file
            
        Returns:
            Recognition results
        """
        if not self.available:
            return {
                "status": "error",
                "message": "Speech Recognition is not available due to missing dependencies"
            }
        
        try:
            # Open audio stream
            stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            logger.info("Listening for speech...")
            print("🎤 Listening... (Speak now)")
            
            # Initialize variables
            frames = []
            silent_chunks = 0
            speech_detected = False
            start_time = time.time()
            
            # Start recording
            while True:
                # Check timeout
                if timeout and time.time() - start_time > timeout:
                    logger.info("Recording stopped due to timeout")
                    break
                
                # Read audio chunk
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                
                # Check for silence
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_data).mean()
                
                if volume > SILENCE_THRESHOLD:
                    silent_chunks = 0
                    speech_detected = True
                else:
                    silent_chunks += 1
                
                # Stop recording if silence is detected for SILENCE_DURATION
                if speech_detected and silent_chunks > RATE / CHUNK * SILENCE_DURATION:
                    logger.info("Recording stopped due to silence detection")
                    break
            
            # Close the stream
            stream.stop_stream()
            stream.close()
            
            # Check if we captured anything meaningful
            audio_length = len(frames) * CHUNK / RATE
            if not speech_detected or audio_length < MIN_AUDIO_LENGTH:
                return {
                    "status": "error",
                    "message": "No speech detected or recording too short"
                }
            
            # Save audio file if requested
            audio_path = None
            if save_audio:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_path = AUDIO_DIR / f"recording_{timestamp}.wav"
                
                with wave.open(str(audio_path), 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                
                logger.info(f"Audio saved to {audio_path}")
            
            # Create a temporary file for processing if we're not saving
            if not audio_path:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    audio_path = Path(temp_file.name)
                    
                    with wave.open(str(audio_path), 'wb') as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(frames))
            
            # Transcribe audio file
            logger.info(f"Transcribing audio with {'OpenAI Whisper' if USING_OPENAI_WHISPER else 'faster-whisper'}...")
            
            # Run the transcription in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            if USING_OPENAI_WHISPER:
                # OpenAI Whisper transcription
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.model.transcribe(str(audio_path))
                )
                
                recognized_text = result["text"].strip()
                detected_language = result.get("language")
                
            elif USING_FASTER_WHISPER:
                # faster-whisper transcription
                # This returns segments and info
                transcribe_func = lambda: self.model.transcribe(
                    str(audio_path),
                    beam_size=5,
                    language=None,  # Let it auto-detect
                    task="transcribe"
                )
                
                segments, info = await loop.run_in_executor(None, transcribe_func)
                
                # Collect all segments
                text_parts = []
                for segment in segments:
                    text_parts.append(segment.text)
                
                recognized_text = " ".join(text_parts).strip()
                detected_language = info.language
            else:
                recognized_text = "Speech recognition failed - no model available"
                detected_language = None
            
            # Clean up temporary file if we created one
            if not save_audio and audio_path:
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    logger.error(f"Error removing temporary file: {str(e)}")
            
            return {
                "status": "success",
                "text": recognized_text,
                "audio_path": str(audio_path) if save_audio else None,
                "language": detected_language,
                "duration": audio_length,
                "model": f"{'OpenAI ' if USING_OPENAI_WHISPER else 'faster-'}whisper-{self.model_size}"
            }
        
        except Exception as e:
            logger.error(f"Error in speech recognition: {str(e)}")
            return {
                "status": "error",
                "message": f"Speech recognition failed: {str(e)}"
            }
    
    async def transcribe_file(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe an existing audio file
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcription results
        """
        if not self.available:
            return {
                "status": "error", 
                "message": "Speech Recognition is not available due to missing dependencies"
            }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    "status": "error",
                    "message": f"Audio file not found: {file_path}"
                }
            
            # Transcribe using the appropriate model
            logger.info(f"Transcribing audio file {file_path} with {'OpenAI Whisper' if USING_OPENAI_WHISPER else 'faster-whisper'}")
            
            # Run the transcription in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            if USING_OPENAI_WHISPER:
                # OpenAI Whisper transcription
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.model.transcribe(file_path)
                )
                
                recognized_text = result["text"].strip()
                detected_language = result.get("language")
                
            elif USING_FASTER_WHISPER:
                # faster-whisper transcription
                transcribe_func = lambda: self.model.transcribe(
                    file_path,
                    beam_size=5,
                    language=None,  # Auto-detect
                    task="transcribe"
                )
                
                segments, info = await loop.run_in_executor(None, transcribe_func)
                
                # Collect all segments
                text_parts = []
                for segment in segments:
                    text_parts.append(segment.text)
                
                recognized_text = " ".join(text_parts).strip()
                detected_language = info.language
            else:
                return {
                    "status": "error",
                    "message": "No transcription model available"
                }
            
            return {
                "status": "success",
                "text": recognized_text,
                "language": detected_language,
                "model": f"{'OpenAI ' if USING_OPENAI_WHISPER else 'faster-'}whisper-{self.model_size}"
            }
        
        except Exception as e:
            logger.error(f"Error transcribing file: {str(e)}")
            return {
                "status": "error",
                "message": f"Transcription failed: {str(e)}"
            }
    
    async def set_model(self, model_size: str) -> Dict[str, Any]:
        """
        Change the Whisper model size
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
            
        Returns:
            Status information
        """
        if not self.available:
            return {
                "status": "error", 
                "message": "Speech Recognition is not available due to missing dependencies"
            }
        
        try:
            valid_sizes = ["tiny", "base", "small", "medium", "large"]
            if model_size not in valid_sizes:
                return {
                    "status": "error",
                    "message": f"Invalid model size. Choose from: {', '.join(valid_sizes)}"
                }
            
            if model_size == self.model_size:
                return {
                    "status": "success",
                    "message": f"Already using {model_size} model"
                }
            
            # Load the new model
            if USING_OPENAI_WHISPER:
                logger.info(f"Loading OpenAI Whisper {model_size} model...")
                
                # Run model loading in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(
                    None,
                    lambda: whisper.load_model(model_size)
                )
            
            elif USING_FASTER_WHISPER:
                logger.info(f"Loading faster-whisper {model_size} model...")
                
                # Run model loading in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                model_load_func = lambda: WhisperModel(model_size, device="auto", compute_type="int8")
                self.model = await loop.run_in_executor(None, model_load_func)
            
            self.model_size = model_size
            logger.info(f"Switched to {'OpenAI ' if USING_OPENAI_WHISPER else 'faster-'}whisper {model_size} model")
            
            return {
                "status": "success",
                "message": f"Switched to {model_size} model",
                "model": f"{'OpenAI ' if USING_OPENAI_WHISPER else 'faster-'}whisper-{model_size}"
            }
        
        except Exception as e:
            logger.error(f"Error changing model: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to change model: {str(e)}"
            }
    
    async def execute(self, command: str = "listen", **kwargs) -> Dict[str, Any]:
        """
        Execute extension commands
        
        Args:
            command: The command to execute
            **kwargs: Command-specific arguments
            
        Returns:
            Command execution results
        """
        if command == "listen":
            return await self.listen(
                timeout=kwargs.get("timeout", 30),
                save_audio=kwargs.get("save_audio", True)
            )
        elif command == "transcribe":
            return await self.transcribe_file(
                file_path=kwargs.get("file_path", "")
            )
        elif command == "set_model":
            return await self.set_model(
                model_size=kwargs.get("model_size", "base")
            )
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}


# Add this extension to the registry
if __name__ == "__main__":
    # This allows for testing the extension directly
    extension = SpeechRecognition()
    print(f"Initialized {extension.name} v{extension.version}")
    print(f"Commands: listen, transcribe, set_model")