#!/usr/bin/env python3
"""
App Tracker Extension for Claude Computer Use API

This extension tracks and analyzes application usage patterns, providing:
- Active application monitoring
- Usage statistics
- Screen time analysis
- Application usage reports
"""

import os
import time
import json
import asyncio
import logging
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

import psutil
import pygetwindow as gw

# Import the extension base class from the parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension_module import Extension

# Configure logging
logger = logging.getLogger('app_tracker')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler('logs/app_tracker.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Constants
DATA_DIR = Path('data/app_tracker')
DEFAULT_POLLING_INTERVAL = 5  # seconds


class AppTracker(Extension):
    """
    Extension for tracking application usage
    """
    
    name = "app_tracker"
    description = "Tracks and analyzes application usage patterns"
    version = "1.0.0"
    author = "Claude Computer Use API Team"
    
    def __init__(self):
        """Initialize the App Tracker extension"""
        super().__init__()
        self.tracking = False
        self.start_time = None
        self.polling_interval = DEFAULT_POLLING_INTERVAL
        self.app_data = {}
        self.active_window_history = []
        self.background_task = None
        
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Load previous data if it exists
        self._load_data()
        
        logger.info("App Tracker extension initialized")
    
    def _load_data(self) -> None:
        """Load tracked app data from disk"""
        data_file = DATA_DIR / 'app_usage.json'
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    self.app_data = data.get('app_data', {})
                    logger.info(f"Loaded app data from {data_file}")
            except Exception as e:
                logger.error(f"Error loading app data: {str(e)}")
    
    def _save_data(self) -> None:
        """Save tracked app data to disk"""
        data_file = DATA_DIR / 'app_usage.json'
        try:
            with open(data_file, 'w') as f:
                json.dump({
                    'app_data': self.app_data,
                    'last_updated': datetime.datetime.now().isoformat()
                }, f, indent=2)
            logger.info(f"Saved app data to {data_file}")
        except Exception as e:
            logger.error(f"Error saving app data: {str(e)}")
    
    async def _track_active_window(self) -> None:
        """Background task to track active window"""
        logger.info("Starting active window tracking")
        self.start_time = time.time()
        
        while self.tracking:
            try:
                # Get active window info
                active_window = gw.getActiveWindow()
                if active_window:
                    app_name = active_window.title
                    
                    # Record this window in history
                    timestamp = time.time()
                    self.active_window_history.append({
                        'app_name': app_name,
                        'timestamp': timestamp,
                        'duration': self.polling_interval
                    })
                    
                    # Update app data
                    if app_name not in self.app_data:
                        self.app_data[app_name] = {
                            'total_time': 0,
                            'session_count': 0,
                            'last_active': timestamp
                        }
                    
                    self.app_data[app_name]['total_time'] += self.polling_interval
                    
                    # Check if this is a new session (more than 60 seconds since last active)
                    if timestamp - self.app_data[app_name].get('last_active', 0) > 60:
                        self.app_data[app_name]['session_count'] += 1
                    
                    self.app_data[app_name]['last_active'] = timestamp
                    
                    # Save data every 10 minutes
                    if len(self.active_window_history) % (600 // self.polling_interval) == 0:
                        self._save_data()
                        
                    logger.debug(f"Active window: {app_name}")
            
            except Exception as e:
                logger.error(f"Error tracking active window: {str(e)}")
            
            await asyncio.sleep(self.polling_interval)
        
        # Final save when tracking stops
        self._save_data()
        logger.info("Stopped active window tracking")
    
    async def start(self, polling_interval: Optional[int] = None) -> Dict[str, Any]:
        """
        Start tracking application usage
        
        Args:
            polling_interval: Optional interval in seconds between checks
            
        Returns:
            Status information
        """
        if self.tracking:
            return {"status": "error", "message": "App tracking is already running"}
        
        if polling_interval:
            self.polling_interval = max(1, min(60, polling_interval))
        
        self.tracking = True
        self.background_task = asyncio.create_task(self._track_active_window())
        
        return {
            "status": "success", 
            "message": f"App tracking started with polling interval of {self.polling_interval}s"
        }
    
    async def stop(self) -> Dict[str, Any]:
        """
        Stop tracking application usage
        
        Returns:
            Status information
        """
        if not self.tracking:
            return {"status": "error", "message": "App tracking is not running"}
        
        self.tracking = False
        if self.background_task:
            await self.background_task
            self.background_task = None
        
        duration = time.time() - self.start_time if self.start_time else 0
        
        return {
            "status": "success",
            "message": f"App tracking stopped after {duration:.2f} seconds",
            "duration": duration
        }
    
    async def status(self) -> Dict[str, Any]:
        """
        Get tracking status
        
        Returns:
            Status information
        """
        if not self.tracking:
            return {"status": "stopped", "message": "App tracking is not running"}
        
        duration = time.time() - self.start_time if self.start_time else 0
        
        return {
            "status": "running",
            "message": f"App tracking has been running for {duration:.2f} seconds",
            "duration": duration,
            "polling_interval": self.polling_interval,
            "app_count": len(self.app_data)
        }
    
    async def report(self, 
                    app_name: Optional[str] = None, 
                    top_n: Optional[int] = 5,
                    days: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate usage report
        
        Args:
            app_name: Optional specific app to report on
            top_n: Number of top apps to include in report
            days: Number of days to include in report
            
        Returns:
            Report data
        """
        if app_name:
            if app_name not in self.app_data:
                return {"status": "error", "message": f"No data for app: {app_name}"}
            
            app_info = self.app_data[app_name]
            return {
                "status": "success",
                "app_name": app_name,
                "total_time": app_info['total_time'],
                "total_time_formatted": self._format_time(app_info['total_time']),
                "session_count": app_info['session_count'],
                "last_active": datetime.datetime.fromtimestamp(app_info['last_active']).isoformat()
            }
        
        # Filter app data by days if specified
        filtered_data = self.app_data
        if days:
            cutoff_time = time.time() - (days * 86400)
            filtered_data = {
                app: data for app, data in self.app_data.items()
                if data.get('last_active', 0) >= cutoff_time
            }
        
        # Sort apps by total time
        sorted_apps = sorted(
            filtered_data.items(),
            key=lambda x: x[1]['total_time'],
            reverse=True
        )
        
        # Get top N apps
        top_apps = sorted_apps[:top_n] if top_n else sorted_apps
        
        return {
            "status": "success",
            "top_apps": [
                {
                    "app_name": app,
                    "total_time": data['total_time'],
                    "total_time_formatted": self._format_time(data['total_time']),
                    "session_count": data['session_count'],
                    "last_active": datetime.datetime.fromtimestamp(data['last_active']).isoformat()
                }
                for app, data in top_apps
            ],
            "total_apps_tracked": len(filtered_data),
            "days_included": days if days else "all"
        }
    
    async def reset(self) -> Dict[str, Any]:
        """
        Reset all tracked data
        
        Returns:
            Status information
        """
        was_tracking = self.tracking
        
        # Stop tracking if running
        if was_tracking:
            await self.stop()
        
        # Reset data
        self.app_data = {}
        self.active_window_history = []
        self._save_data()
        
        # Restart tracking if it was running
        if was_tracking:
            await self.start(self.polling_interval)
        
        return {"status": "success", "message": "All app tracking data has been reset"}
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into a readable time string"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    async def execute(self, command: str = "status", **kwargs) -> Dict[str, Any]:
        """
        Execute extension commands
        
        Args:
            command: The command to execute
            **kwargs: Command-specific arguments
            
        Returns:
            Command execution results
        """
        if command == "start":
            return await self.start(kwargs.get("polling_interval"))
        elif command == "stop":
            return await self.stop()
        elif command == "status":
            return await self.status()
        elif command == "report":
            return await self.report(
                app_name=kwargs.get("app_name"),
                top_n=kwargs.get("top_n", 5),
                days=kwargs.get("days")
            )
        elif command == "reset":
            return await self.reset()
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}


# Add this extension to the registry
if __name__ == "__main__":
    # This allows for testing the extension directly
    extension = AppTracker()
    print(f"Initialized {extension.name} v{extension.version}")
    print(f"Commands: start, stop, status, report, reset")