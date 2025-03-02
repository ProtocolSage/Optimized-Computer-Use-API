# Claude Computer Use API

An optimized implementation of the Claude Computer Use API for Windows 11, with a modern GUI interface and an extensible plugin architecture.

![Claude Computer Use API](https://img.shields.io/badge/Claude-Computer%20Use%20API-5A67D8)
![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Windows 11](https://img.shields.io/badge/Platform-Windows%2011-0078D6.svg)
![License MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

This project provides a streamlined implementation of the Computer Use API for Claude, optimized for modern Windows 11 systems. It allows Claude to control and interact with your computer through a set of carefully designed tools that enable:

- **Keyboard and mouse control** for application interaction
- **Screenshot capabilities** for visual feedback
- **File system operations** for creating and editing files
- **Command execution** for running system commands
- **Extensible architecture** for adding custom functionality

## Features

- 🖥️ **Intuitive GUI Interface**: User-friendly interface with chat history, screenshot display, and command input
- 🧩 **Extension System**: Modular plugin architecture for adding new capabilities
- 🔒 **Security Controls**: Configurable security levels with command approval
- 🎤 **Voice Interaction**: Speak to Claude with speech recognition and hear responses via text-to-speech
- 📊 **App Tracking**: Track and analyze application usage (via extension)
- 🔍 **Web Search**: Search the web and retrieve information (via extension)
- 🗣️ **Text-to-Speech**: Convert text to speech for voice feedback (via extension)
- 🎙️ **Speech Recognition**: Convert speech to text using OpenAI's Whisper model (via extension)
- 📱 **Notifications**: Send desktop notifications (via extension)
- 📝 **Logging**: Detailed logging for monitoring and debugging

## Quick Start

1. **Clone or download** this repository
2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
   
   Note: For speech recognition, we now support both:
   - **OpenAI Whisper**: More accurate but slower, requires more resources
   - **faster-whisper**: Much faster performance, especially on GPU systems

3. **Set your API key**:
   ```powershell
   setx ANTHROPIC_API_KEY "your_api_key_here"
   ```
4. **Run the GUI**:
   ```powershell
   python gui_wrapper.py
   ```

## System Requirements

- Windows 11 (build 26100.3194 or later)
- Python 3.9+ installed
- Anthropic API key with Computer Use permissions
- Claude 3.5 Sonnet model access
- Administrative privileges (for initial setup)
- Microphone (for voice interaction features)
- Speakers or headphones (for text-to-speech features)

## Directory Structure

```
C:\Claude-Computer-API\
│
├── computer_use_api.py         # Core API implementation
├── extension_module.py         # Extension system
├── api_integration.py          # Integration module
├── gui_wrapper.py              # GUI application
├── quick_setup.py              # Setup script
├── voice_interaction.py        # Voice interaction module
│
├── config\                     # Configuration files
│   └── voice_config.json       # Voice interaction settings
├── extensions\                 # Built-in extensions
│   ├── web_search.py           # Web search extension
│   ├── text_to_speech.py       # Text-to-speech extension
│   └── speech_recognition.py   # Speech recognition extension
├── custom_extensions\          # Your custom extensions
├── data\                       # Data storage for extensions
│   └── speech_recognition\     # Recorded speech files
├── logs\                       # Log files
└── outputs\                    # Screenshots and other outputs
```

## Installation

### Automatic Setup

Run the included setup script to create the necessary directory structure and install dependencies:

```powershell
python quick_setup.py
```

### Manual Setup

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
   pip install anthropic pyautogui httpx pillow pyttsx3 requests psutil pygetwindow win10toast pyaudio numpy openai-whisper
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

## Usage

### GUI Application

For most users, the GUI application is the easiest way to interact with Claude:

```powershell
python gui_wrapper.py
```

### Voice Interaction

The GUI includes voice interaction capabilities:

- Use the "Voice Interaction" checkbox to toggle continuous listening mode
- Click the "🎤 Speak" button to speak a single command
- Configure voice settings in the "Voice" menu
- Choose between different Whisper models and TTS settings

### Command Line Interface

For basic usage or automation scenarios:

```powershell
python computer_use_api.py
```

### Extension Commands

You can use special commands to interact with extensions:

- `/ext list` - List all available extensions
- `/ext help` - Show help for extension commands
- `/ext [extension_name] [command] [args]` - Execute an extension command

Examples:
- `/ext web_search query="Claude AI capabilities"`
- `/ext text_to_speech text="Hello, world!" rate=150`
- `/ext app_tracker start`
- `/ext speech_recognition listen timeout=30`

## Creating Custom Extensions

You can easily extend the functionality by creating custom extensions:

1. Create a new Python file in the `custom_extensions` directory
2. Import the `Extension` base class
3. Implement the required methods

Example:

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

This implementation gives Claude direct control over your computer, which requires careful security considerations:

- Use appropriate security levels based on your environment
- Monitor Claude's actions while it's controlling your computer
- Review logs regularly to track all performed actions
- Consider running in a limited user account for sensitive operations

For detailed security information, see [SECURITY.md](SECURITY.md).

## Documentation

- [Comprehensive Setup and Usage Guide](docs/comprehensive-guide.md)
- [Extension Development Guide](docs/extension-development.md)
- [API Reference](docs/api-reference.md)
- [Security Guide](docs/security-guide.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Anthropic for creating Claude and the Computer Use API
- OpenAI for the Whisper speech recognition model
- Contributors to the Python libraries used in this project
- Everyone who has provided feedback and suggestions

---

**Note**: This implementation is not officially affiliated with or endorsed by Anthropic. Always use the Computer Use API responsibly and in accordance with Anthropic's terms of service.