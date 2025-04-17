"""
Sample custom extension for the Computer Use API.
This file should be placed in the 'extensions' directory.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Import the Extension base class
try:
    from extension_module import Extension
except ImportError:
    # If running directly or in a different directory structure
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from extension_module import Extension

logger = logging.getLogger("app_tracker_extension")

class AppTrackerExtension(Extension):
    """Extension for tracking application usage."""
    
    name = "app_tracker"
    description = "Tracks application usage and provides statistics"
    version = "1.0.0"
    author = "Claude API Team"
    
    def __init__(self):
        super().__init__()
        self.app_data_file = os.path.join("data", "app_tracking.json")
        self.tracking_data = self._load_tracking_data()
        self._currently_tracking = False
        self._track_task = None
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.app_data_file), exist_ok=True)
    
    def _load_tracking_data(self) -> Dict[str, Any]:
        """Load tracking data from file."""
        if os.path.exists(self.app_data_file):
            try:
                with open(self.app_data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading tracking data: {str(e)}")
        
        # Initialize with empty data if file doesn't exist or has errors
        return {
            "apps": {},
            "sessions": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_tracking_data(self) -> None:
        """Save tracking data to file."""
        try:
            # Update the last updated timestamp
            self.tracking_data["last_updated"] = datetime.now().isoformat()
            
            with open(self.app_data_file, 'w') as f:
                json.dump(self.tracking_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tracking data: {str(e)}")
    
    async def start_tracking(self) -> None:
        """Start tracking application usage."""
        if self._currently_tracking:
            return
        
        self._currently_tracking = True
        self._track_task = asyncio.create_task(self._tracking_loop())
        
        # Record the start of a new session
        session_id = f"session_{len(self.tracking_data['sessions']) + 1}"
        self.tracking_data["sessions"].append({
            "id": session_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "apps": []
        })
        
        logger.info(f"Started application tracking session: {session_id}")
    
    async def stop_tracking(self) -> None:
        """Stop tracking application usage."""
        if not self._currently_tracking:
            return
        
        self._currently_tracking = False
        if self._track_task:
            self._track_task.cancel()
            try:
                await self._track_task
            except asyncio.CancelledError:
                pass
        
        # Record the end of the current session
        if self.tracking_data["sessions"]:
            current_session = self.tracking_data["sessions"][-1]
            current_session["end_time"] = datetime.now().isoformat()
            
            # Calculate duration
            start_time = datetime.fromisoformat(current_session["start_time"])
            end_time = datetime.fromisoformat(current_session["end_time"])
            duration = (end_time - start_time).total_seconds()
            current_session["duration_seconds"] = duration
            
            logger.info(f"Stopped application tracking session: {current_session['id']}")
        
        # Save the tracking data
        self._save_tracking_data()
    
    async def _tracking_loop(self) -> None:
        """Main tracking loop."""
        try:
            while self._currently_tracking:
                # Get the current active window
                current_app = await self._get_current_app()
                
                # Update tracking data
                if current_app:
                    app_name = current_app["name"]
                    app_title = current_app["title"]
                    
                    # Update apps dictionary
                    if app_name not in self.tracking_data["apps"]:
                        self.tracking_data["apps"][app_name] = {
                            "total_time_seconds": 0,
                            "last_seen": datetime.now().isoformat(),
                            "titles": []
                        }
                    
                    app_data = self.tracking_data["apps"][app_name]
                    app_data["total_time_seconds"] += 1  # Increment by 1 second
                    app_data["last_seen"] = datetime.now().isoformat()
                    
                    # Add title if not already tracked
                    if app_title and app_title not in app_data["titles"]:
                        app_data["titles"].append(app_title)
                    
                    # Update current session
                    if self.tracking_data["sessions"]:
                        current_session = self.tracking_data["sessions"][-1]
                        # Add to apps list if not already there
                        if app_name not in current_session["apps"]:
                            current_session["apps"].append(app_name)
                
                # Save data periodically (every minute)
                if datetime.now().second == 0:
                    self._save_tracking_data()
                
                # Wait for next check
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Tracking loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in tracking loop: {str(e)}")
            self._currently_tracking = False
    
    async def _get_current_app(self) -> Optional[Dict[str, str]]:
        """Get the currently active application window."""
        try:
            import psutil
            import pygetwindow as gw
            
            # Get active window
            active_window = gw.getActiveWindow()
            if not active_window:
                return None
            
            app_title = active_window.title
            
            # Get process details
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.pid == active_window._hWnd:  # Direct match
                        return {
                            "name": proc.info['name'],
                            "title": app_title,
                            "pid": proc.pid
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # If direct match fails, use the window title to guess
            return {
                "name": app_title.split(' - ')[-1] if ' - ' in app_title else app_title,
                "title": app_title,
                "pid": None
            }
        except ImportError:
            logger.warning("AppTracker requires 'psutil' and 'pygetwindow'. Install using: pip install psutil pygetwindow")
            return None
        except Exception as e:
            logger.error(f"Error getting current app: {str(e)}")
            return None
    
    async def execute(self, command: str = "stats", **kwargs) -> Dict[str, Any]:
        """Execute commands for the app tracker extension."""
        command = command.lower()
        
        if command == "start":
            await self.start_tracking()
            return {"status": "Tracking started", "success": True}
        
        elif command == "stop":
            await self.stop_tracking()
            return {"status": "Tracking stopped", "success": True}
        
        elif command == "status":
            return {
                "tracking": self._currently_tracking,
                "apps_tracked": len(self.tracking_data["apps"]),
                "sessions": len(self.tracking_data["sessions"]),
                "success": True
            }
        
        elif command == "stats":
            # Get statistics about app usage
            app_stats = []
            for app_name, app_data in self.tracking_data["apps"].items():
                # Convert seconds to hours/minutes/seconds
                total_seconds = app_data["total_time_seconds"]
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                app_stats.append({
                    "name": app_name,
                    "total_time": {
                        "hours": hours,
                        "minutes": minutes,
                        "seconds": seconds,
                        "total_seconds": total_seconds
                    },
                    "last_seen": app_data["last_seen"],
                    "title_count": len(app_data["titles"]),
                    "titles": app_data["titles"][:5]  # Limit to first 5 titles
                })
            
            # Sort by total time (descending)
            app_stats.sort(key=lambda x: x["total_time"]["total_seconds"], reverse=True)
            
            # Get session statistics
            session_stats = []
            for session in self.tracking_data["sessions"]:
                # Calculate duration if session has ended
                if session["end_time"]:
                    start_time = datetime.fromisoformat(session["start_time"])
                    end_time = datetime.fromisoformat(session["end_time"])
                    duration = (end_time - start_time).total_seconds()
                else:
                    # For active session, calculate against current time
                    start_time = datetime.fromisoformat(session["start_time"])
                    duration = (datetime.now() - start_time).total_seconds()
                
                # Format duration
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                seconds = int(duration % 60)
                
                session_stats.append({
                    "id": session["id"],
                    "start_time": session["start_time"],
                    "end_time": session["end_time"],
                    "duration": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                    "duration_seconds": duration,
                    "app_count": len(session["apps"]),
                    "apps": session["apps"][:5]  # Limit to first 5 apps
                })
            
            return {
                "top_apps": app_stats[:10],  # Top 10 apps
                "total_apps_tracked": len(self.tracking_data["apps"]),
                "sessions": session_stats,
                "total_tracking_time": sum(app["total_time"]["total_seconds"] for app in app_stats),
                "success": True
            }
        
        elif command == "clear":
            # Reset tracking data
            self.tracking_data = {
                "apps": {},
                "sessions": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_tracking_data()
            return {"status": "Tracking data cleared", "success": True}
        
        elif command == "report":
            # Generate a detailed report
            report_format = kwargs.get("format", "text")
            limit = kwargs.get("limit", 10)
            
            if report_format == "json":
                # Return raw JSON data (limited)
                return {
                    "apps": list(self.tracking_data["apps"].items())[:limit],
                    "sessions": self.tracking_data["sessions"][:limit],
                    "last_updated": self.tracking_data["last_updated"],
                    "success": True
                }
            else:
                # Generate text report
                report = []
                report.append("APPLICATION USAGE REPORT")
                report.append("======================\n")
                
                report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                report.append(f"Total Apps Tracked: {len(self.tracking_data['apps'])}")
                report.append(f"Total Sessions: {len(self.tracking_data['sessions'])}\n")
                
                report.append("TOP APPLICATIONS BY USAGE TIME")
                report.append("-----------------------------")
                for i, (app_name, app_data) in enumerate(
                    sorted(
                        self.tracking_data["apps"].items(),
                        key=lambda x: x[1]["total_time_seconds"],
                        reverse=True
                    )[:limit],
                    1
                ):
                    total_seconds = app_data["total_time_seconds"]
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    
                    report.append(f"{i}. {app_name}")
                    report.append(f"   Total Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
                    report.append(f"   Last Seen: {app_data['last_seen']}")
                    if app_data["titles"]:
                        report.append(f"   Window Titles: {', '.join(app_data['titles'][:3])}")
                    report.append("")
                
                report.append("RECENT SESSIONS")
                report.append("--------------")
                for i, session in enumerate(reversed(self.tracking_data["sessions"][:limit]), 1):
                    report.append(f"{i}. {session['id']}")
                    report.append(f"   Start: {session['start_time']}")
                    report.append(f"   End: {session['end_time'] or 'Active'}")
                    
                    if session["end_time"]:
                        start_time = datetime.fromisoformat(session["start_time"])
                        end_time = datetime.fromisoformat(session["end_time"])
                        duration = (end_time - start_time).total_seconds()
                    else:
                        start_time = datetime.fromisoformat(session["start_time"])
                        duration = (datetime.now() - start_time).total_seconds()
                    
                    hours = int(duration // 3600)
                    minutes = int((duration % 3600) // 60)
                    seconds = int(duration % 60)
                    
                    report.append(f"   Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
                    report.append(f"   Apps Used: {', '.join(session['apps'][:5])}")
                    report.append("")
                
                return {
                    "report": "\n".join(report),
                    "success": True
                }
        
        else:
            return {"error": f"Unknown command: {command}", "success": False}
