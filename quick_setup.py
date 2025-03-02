"""
Quick setup script for the Claude Computer Use API.
This script automates the installation and configuration process.
"""

import os
import sys
import subprocess
import shutil
import json
import getpass
from pathlib import Path
import pkg_resources

# Define constants
DEFAULT_INSTALL_DIR = os.path.join(os.path.expanduser("~"), "Claude-Computer-API")
REQUIRED_PACKAGES = [
    "anthropic>=0.5.0",
    "pyautogui>=0.9.53",
    "httpx>=0.24.0",
    "pillow>=9.0.0",
    "pyttsx3>=2.90",
    "requests>=2.28.0",
    "psutil>=5.9.0",
    "pygetwindow>=0.0.9",
    "win10toast>=0.9; platform_system=='Windows'",
    "notify2>=0.3; platform_system=='Linux'",
]
REQUIRED_DIRECTORIES = [
    "config",
    "extensions",
    "custom_extensions",
    "data",
    "logs",
    "outputs",
]

# Colors for console output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== {text} ==={Colors.ENDC}\n")

def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_info(text):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def create_directories(base_path):
    """Create all required directories."""
    print_header("Creating Directories")
    
    for directory in REQUIRED_DIRECTORIES:
        dir_path = os.path.join(base_path, directory)
        try:
            os.makedirs(dir_path, exist_ok=True)
            print_success(f"Created directory: {directory}")
        except Exception as e:
            print_error(f"Failed to create directory {directory}: {str(e)}")
            return False
    
    return True

def install_dependencies():
    """Install required Python packages."""
    print_header("Installing Dependencies")
    
    # Check for pip
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print_error("pip not found. Please install pip first.")
        return False
    
    # Get currently installed packages
    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    
    # Install missing packages
    for package in REQUIRED_PACKAGES:
        package_name = package.split(">=")[0].split(";")[0].strip()
        
        if package_name.lower() in installed_packages:
            print_info(f"Package already installed: {package_name} (version {installed_packages[package_name.lower()]})")
            continue
        
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package],
                                 stdout=subprocess.DEVNULL)
            print_success(f"Installed package: {package}")
        except subprocess.CalledProcessError:
            print_error(f"Failed to install package: {package}")
            return False
    
    return True

def create_config_files(base_path):
    """Create necessary configuration files."""
    print_header("Creating Configuration Files")
    
    # Create extensions.json
    extensions_config = {
        "extension_dirs": [
            "extensions",
            "custom_extensions"
        ],
        "extensions": {
            "web_search": {
                "enabled": True,
                "max_results": 5
            },
            "text_to_speech": {
                "enabled": True,
                "rate": 150,
                "volume": 0.8
            },
            "notification": {
                "enabled": True
            },
            "app_tracker": {
                "enabled": True
            }
        }
    }
    
    try:
        config_path = os.path.join(base_path, "config", "extensions.json")
        with open(config_path, 'w') as f:
            json.dump(extensions_config, f, indent=2)
        print_success("Created extensions.json configuration")
    except Exception as e:
        print_error(f"Failed to create extensions.json: {str(e)}")
        return False
    
    # Create .env file template
    try:
        env_path = os.path.join(base_path, ".env.template")
        with open(env_path, 'w') as f:
            f.write("# Environment variables for Claude Computer Use API\n")
            f.write("# Rename this file to .env and fill in your API key\n\n")
            f.write("ANTHROPIC_API_KEY=your_api_key_here\n")
        print_success("Created .env.template file")
    except Exception as e:
        print_error(f"Failed to create .env.template: {str(e)}")
    
    # Set up API key
    api_key = input("\nEnter your Anthropic API key (leave blank to skip): ").strip()
    if api_key:
        try:
            # Save to config file
            key_path = os.path.join(base_path, "config", "api_key.txt")
            with open(key_path, 'w') as f:
                f.write(api_key)
            os.chmod(key_path, 0o600)  # Restrict file permissions
            print_success("Saved API key to config/api_key.txt")
            
            # Set environment variable for current session
            os.environ["ANTHROPIC_API_KEY"] = api_key
            print_info("Set ANTHROPIC_API_KEY environment variable for current session")
            
            # Create .env file
            env_path = os.path.join(base_path, ".env")
            with open(env_path, 'w') as f:
                f.write(f"ANTHROPIC_API_KEY={api_key}\n")
            os.chmod(env_path, 0o600)  # Restrict file permissions
            print_success("Created .env file with API key")
            
            # Attempt to set permanent environment variable (Windows only)
            if os.name == 'nt':
                try:
                    subprocess.run(["setx", "ANTHROPIC_API_KEY", api_key], 
                                  check=True, 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
                    print_success("Set ANTHROPIC_API_KEY as a permanent environment variable")
                except subprocess.CalledProcessError:
                    print_warning("Could not set permanent environment variable. You may need administrative privileges.")
                    print_info("You can manually set the environment variable or use the .env file.")
            
        except Exception as e:
            print_error(f"Failed to save API key: {str(e)}")
    else:
        print_info("API key setup skipped. You'll need to set it later.")
    
    return True

def create_example_extension(base_path):
    """Create an example custom extension."""
    print_header("Creating Example Extension")
    
    example_code = """\"\"\"
Example custom extension for the Claude Computer Use API.
\"\"\"

import os
import asyncio
from datetime import datetime

# Import the Extension base class
try:
    from extension_module import Extension
except ImportError:
    # If running directly or in a different directory structure
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from extension_module import Extension

class HelloWorldExtension(Extension):
    \"\"\"Simple hello world extension example.\"\"\"
    
    name = "hello_world"
    description = "A simple example extension that says hello"
    version = "1.0.0"
    author = "You"
    
    def __init__(self):
        super().__init__()
        self.greeting_count = 0
    
    async def execute(self, command="greet", **kwargs):
        \"\"\"Execute the extension functionality.\"\"\"
        if command == "greet":
            name = kwargs.get("name", "World")
            self.greeting_count += 1
            return {
                "message": f"Hello, {name}!",
                "timestamp": datetime.now().isoformat(),
                "greeting_count": self.greeting_count,
                "success": True
            }
        elif command == "info":
            return {
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "author": self.author,
                "greeting_count": self.greeting_count,
                "success": True
            }
        else:
            return {
                "error": f"Unknown command: {command}",
                "success": False
            }

# Example usage if this file is run directly
if __name__ == "__main__":
    async def test_extension():
        ext = HelloWorldExtension()
        result1 = await ext.execute("greet", name="Claude")
        print(f"Greeting result: {result1}")
        
        result2 = await ext.execute("info")
        print(f"Info result: {result2}")
        
        result3 = await ext.execute("greet")
        print(f"Default greeting result: {result3}")
    
    asyncio.run(test_extension())
"""
    
    try:
        example_path = os.path.join(base_path, "custom_extensions", "hello_world.py")
        with open(example_path, 'w') as f:
            f.write(example_code)
        print_success("Created example extension: hello_world.py")
    except Exception as e:
        print_error(f"Failed to create example extension: {str(e)}")
        return False
    
    return True

def create_shortcut(base_path):
    """Create desktop shortcut (Windows only)."""
    if os.name != 'nt':
        return True
    
    print_header("Creating Desktop Shortcut")
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "Claude Computer API.lnk")
        
        target = os.path.join(sys.executable)
        gui_script = os.path.join(base_path, "gui_wrapper.py")
        wdir = base_path
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target
        shortcut.Arguments = gui_script
        shortcut.WorkingDirectory = wdir
        shortcut.save()
        
        print_success("Created desktop shortcut: Claude Computer API")
    except ImportError:
        print_warning("Could not create desktop shortcut. The pywin32 and winshell packages are required.")
        print_info("You can install them with: pip install pywin32 winshell")
    except Exception as e:
        print_error(f"Failed to create desktop shortcut: {str(e)}")
        print_info("You can still run the application by executing gui_wrapper.py")
    
    return True

def check_system_compatibility():
    """Check if the system is compatible with the application."""
    print_header("Checking System Compatibility")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print_error(f"Python 3.9+ required, but found {python_version.major}.{python_version.minor}")
        print_info("Please upgrade your Python installation: https://www.python.org/downloads/")
        return False
    else:
        print_success(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check OS
    if os.name != 'nt':
        print_warning("This application is optimized for Windows 11, but may work on other platforms")
    else:
        import platform
        win_version = platform.version()
        win_release = platform.release()
        
        if win_release == '10' and int(win_version.split('.')[2]) >= 22000:
            print_success(f"Windows 11 detected (build {win_version})")
        elif win_release == '10':
            print_warning(f"Windows 10 detected (build {win_version}). Some features may not work correctly.")
        else:
            print_warning(f"Windows {win_release} detected. The application is optimized for Windows 11.")
    
    return True

def main():
    """Main setup function."""
    print("\n" + Colors.BOLD + Colors.HEADER + "Claude Computer Use API Setup" + Colors.ENDC + "\n")
    print("This script will set up the Claude Computer Use API on your system.")
    print("It will create necessary directories, install dependencies, and configure the application.")
    
    # Get installation directory
    install_dir = input(f"\nEnter installation directory (default: {DEFAULT_INSTALL_DIR}): ").strip()
    if not install_dir:
        install_dir = DEFAULT_INSTALL_DIR
    
    install_dir = os.path.abspath(install_dir)
    print_info(f"Installation directory: {install_dir}")
    
    # Confirm if directory exists
    if os.path.exists(install_dir):
        if os.listdir(install_dir):
            confirm = input(f"Directory exists and is not empty. Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                print_info("Setup cancelled.")
                return
    
    # Run setup steps
    if not check_system_compatibility():
        print_error("System compatibility check failed.")
        return
    
    try:
        os.makedirs(install_dir, exist_ok=True)
    except Exception as e:
        print_error(f"Failed to create installation directory: {str(e)}")
        return
    
    # Change to installation directory
    original_dir = os.getcwd()
    os.chdir(install_dir)
    
    if not install_dependencies():
        print_error("Failed to install dependencies. Setup aborted.")
        os.chdir(original_dir)
        return
    
    if not create_directories(install_dir):
        print_error("Failed to create directories. Setup aborted.")
        os.chdir(original_dir)
        return
    
    if not create_config_files(install_dir):
        print_error("Failed to create configuration files. Setup aborted.")
        os.chdir(original_dir)
        return
    
    if not create_example_extension(install_dir):
        print_warning("Failed to create example extension, but continuing setup.")
    
    create_shortcut(install_dir)
    
    print_header("Setup Complete")
    print_success("The Claude Computer Use API has been successfully set up!")
    print_info(f"Installation directory: {install_dir}")
    print("\nNext steps:")
    print(f"1. Navigate to the installation directory: cd {install_dir}")
    print("2. Run the GUI application: python gui_wrapper.py")
    print("3. Or run the command-line interface: python computer_use_api.py")
    print("\nFor more information, see the README.md and documentation files.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
