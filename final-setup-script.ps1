# PowerShell script to set up the Docker environment for Claude Computer Use API
# Optimized for Windows 11 with Intel i3-1215U processor and 32GB RAM

# Text colors for console output
function Write-ColorText {
    param (
        [string] $Text,
        [string] $Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

function Write-Header {
    param ([string] $Text)
    Write-Host ""
    Write-Host "=== $Text ===" -ForegroundColor Magenta -BackgroundColor Black
    Write-Host ""
}

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-ColorText "WARNING: This script is not running with administrator privileges." "Yellow"
    Write-ColorText "Some operations might fail. Consider rerunning as administrator." "Yellow"
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}

# Check if Docker is installed
Write-Header "Checking Docker Installation"
try {
    $docker = docker --version
    Write-ColorText "Docker is installed: $docker" "Green"
} catch {
    Write-ColorText "Docker is not installed or not in PATH" "Red"
    Write-ColorText "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" "Yellow"
    exit
}

# Create project directory structure
Write-Header "Creating Project Directory"
$projectDir = "C:\Users\Pablo\Claude-Computer-Use-API"
New-Item -Path $projectDir -ItemType Directory -Force | Out-Null
Set-Location $projectDir

# Create subdirectories
$directories = @("config", "data", "logs", "outputs", "custom_extensions", "extensions", "docs")
foreach ($dir in $directories) {
    New-Item -Path "$projectDir\$dir" -ItemType Directory -Force | Out-Null
    Write-ColorText "Created directory: $dir" "Green"
}

# Copy Docker files
Write-Header "Creating Docker Configuration Files"

# Create Dockerfile
$dockerfilePath = "$projectDir\Dockerfile"
if (Test-Path $dockerfilePath) {
    Write-ColorText "Dockerfile already exists. Overwrite? (y/n)" "Yellow"
    $overwrite = Read-Host
    if ($overwrite -ne "y") {
        Write-ColorText "Skipping Dockerfile creation" "Yellow"
    } else {
        # Copy Dockerfile content to the file
        @'
FROM python:3.11-slim

# Set up environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    xterm \
    xdotool \
    scrot \
    imagemagick \
    novnc \
    websockify \
    tint2 \
    mutter \
    libgl1-mesa-glx \
    firefox-esr \
    sudo \
    net-tools \
    netcat-openbsd \
    curl \
    wget \
    unzip \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash -d /home/appuser appuser
RUN echo "appuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Create directories
RUN mkdir -p /app/config /app/extensions /app/custom_extensions /app/data /app/logs /app/outputs /app/docs

# Copy requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application files
COPY *.py /app/
COPY docs/ /app/docs/
COPY extensions/ /app/extensions/
COPY custom_extensions/ /app/custom_extensions/

# Set ownership
RUN chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Switch to non-root user
USER appuser

# Expose ports for VNC, NoVNC, and streamlit
EXPOSE 5900 6080 8501 8080

# Create startup script
RUN echo '#!/bin/bash \n\
Xvfb :1 -screen 0 1024x768x24 & \n\
sleep 1 \n\
x11vnc -display :1 -forever -shared -rfbport 5900 -bg -xkb -nopw & \n\
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen 6080 & \n\
tint2 & \n\
sleep 2 \n\
python /app/gui_wrapper.py \n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
'@ | Set-Content -Path $dockerfilePath
        Write-ColorText "Created Dockerfile" "Green"
    }
} else {
    # Copy Dockerfile content to the file
    @'
FROM python:3.11-slim

# Set up environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    xterm \
    xdotool \
    scrot \
    imagemagick \
    novnc \
    websockify \
    tint2 \
    mutter \
    libgl1-mesa-glx \
    firefox-esr \
    sudo \
    net-tools \
    netcat-openbsd \
    curl \
    wget \
    unzip \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash -d /home/appuser appuser
RUN echo "appuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Create directories
RUN mkdir -p /app/config /app/extensions /app/custom_extensions /app/data /app/logs /app/outputs /app/docs

# Copy requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application files
COPY *.py /app/
COPY docs/ /app/docs/
COPY extensions/ /app/extensions/
COPY custom_extensions/ /app/custom_extensions/

# Set ownership
RUN chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Switch to non-root user
USER appuser

# Expose ports for VNC, NoVNC, and streamlit
EXPOSE 5900 6080 8501 8080

# Create startup script
RUN echo '#!/bin/bash \n\
Xvfb :1 -screen 0 1024x768x24 & \n\
sleep 1 \n\
x11vnc -display :1 -forever -shared -rfbport 5900 -bg -xkb -nopw & \n\
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen 6080 & \n\
tint2 & \n\
sleep 2 \n\
python /app/gui_wrapper.py \n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
'@ | Set-Content -Path $dockerfilePath
    Write-ColorText "Created Dockerfile" "Green"
}

# Create docker-compose.yml
$dockerComposePath = "$projectDir\docker-compose.yml"
if (Test-Path $dockerComposePath) {
    Write-ColorText "docker-compose.yml already exists. Overwrite? (y/n)" "Yellow"
    $overwrite = Read-Host
    if ($overwrite -ne "y") {
        Write-ColorText "Skipping docker-compose.yml creation" "Yellow"
    } else {
        # Copy docker-compose.yml content to the file
        @'
version: '3.8'

services:
  claude-computer-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: claude-computer-api
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
      - ./outputs:/app/outputs
      - ./custom_extensions:/app/custom_extensions
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DISPLAY=:1
      - MEMORY_LIMIT=24g
      - CPU_LIMIT=6
    ports:
      - "5900:5900"  # VNC
      - "6080:6080"  # noVNC web access
      - "8501:8501"  # Streamlit interface
      - "8080:8080"  # Combined interface
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '6'
          memory: 24G
        reservations:
          cpus: '2'
          memory: 4G
    shm_size: 2gb
    security_opt:
      - no-new-privileges=true
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
'@ | Set-Content -Path $dockerComposePath
        Write-ColorText "Created docker-compose.yml" "Green"
    }
} else {
    # Copy docker-compose.yml content to the file
    @'
version: '3.8'

services:
  claude-computer-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: claude-computer-api
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
      - ./outputs:/app/outputs
      - ./custom_extensions:/app/custom_extensions
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DISPLAY=:1
      - MEMORY_LIMIT=24g
      - CPU_LIMIT=6
    ports:
      - "5900:5900"  # VNC
      - "6080:6080"  # noVNC web access
      - "8501:8501"  # Streamlit interface
      - "8080:8080"  # Combined interface
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '6'
          memory: 24G
        reservations:
          cpus: '2'
          memory: 4G
    shm_size: 2gb
    security_opt:
      - no-new-privileges=true
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
'@ | Set-Content -Path $dockerComposePath
    Write-ColorText "Created docker-compose.yml" "Green"
}

# Create requirements.txt
$requirementsPath = "$projectDir\requirements.txt"
if (Test-Path $requirementsPath) {
    Write-ColorText "requirements.txt already exists. Overwrite? (y/n)" "Yellow"
    $overwrite = Read-Host
    if ($overwrite -ne "y") {
        Write-ColorText "Skipping requirements.txt creation" "Yellow"
    } else {
        # Copy requirements.txt content to the file
        @'
anthropic>=0.6.0
pyautogui>=0.9.53
httpx>=0.24.0
pillow>=9.0.0
pyttsx3>=2.90
requests>=2.28.0
psutil>=5.9.0
pygetwindow>=0.0.9
streamlit>=1.28.0
python-dotenv>=1.0.0
tk>=0.1.0
Pympler>=1.0.1
memory-profiler>=0.61
nest-asyncio>=1.5.8
watchdog>=3.0.0
setuptools>=68.0.0
wheel>=0.41.0
pyOpenSSL>=23.2.0
'@ | Set-Content -Path $requirementsPath
        Write-ColorText "Created requirements.txt" "Green"
    }
} else {
    # Copy requirements.txt content to the file
    @'
anthropic>=0.6.0
pyautogui>=0.9.53
httpx>=0.24.0
pillow>=9.0.0
pyttsx3>=2.90
requests>=2.28.0
psutil>=5.9.0
pygetwindow>=0.0.9
streamlit>=1.28.0
python-dotenv>=1.0.0
tk>=0.1.0
Pympler>=1.0.1
memory-profiler>=0.61
nest-asyncio>=1.5.8
watchdog>=3.0.0
setuptools>=68.0.0
wheel>=0.41.0
pyOpenSSL>=23.2.0
'@ | Set-Content -Path $requirementsPath
    Write-ColorText "Created requirements.txt" "Green"
}

# Create .env file for API key
$envPath = "$projectDir\.env"
if (-not (Test-Path $envPath)) {
    Write-Header "Setting Up API Key"
    $api
}