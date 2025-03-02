import asyncio
import os
import sys
import base64
import json
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, messagebox
from tkinter.font import Font
from io import BytesIO
from PIL import Image, ImageTk
import threading
from datetime import datetime

# Import the Computer Use API module
# Make sure computer_use_api.py is in the same directory
try:
    from computer_use_api import ComputerUseAPI, ToolResult
    from voice_interaction import VoiceInteraction
except ImportError as e:
    print(f"Error: Import failed: {e}")
    sys.exit(1)

class ComputerUseGUI:
    """
    GUI wrapper for the Computer Use API.
    Provides a user-friendly interface for interacting with Claude.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Computer Use API")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Define modern color palette
        self.COLORS = {
            "bg_primary": "#f8f9fa",       # Light background
            "bg_secondary": "#ffffff",     # White background
            "accent": "#5A67D8",           # Purple accent (from README badge)
            "text_primary": "#212529",     # Dark text
            "text_secondary": "#6c757d",   # Gray text
            "success": "#28a745",          # Green
            "info": "#0dcaf0",             # Cyan
            "warning": "#ffc107",          # Yellow
            "danger": "#dc3545",           # Red
            "light_accent": "#e9ecef"      # Light gray for highlights
        }
        
        # Define consistent padding
        self.PADDING = {
            "small": 5,
            "medium": 10,
            "large": 15
        }
        
        # Set up modern styles
        self.style = ttk.Style()
        
        # Configure basic elements
        self.style.configure("TFrame", background=self.COLORS["bg_primary"])
        self.style.configure("TLabelframe", background=self.COLORS["bg_primary"])
        self.style.configure("TLabelframe.Label", background=self.COLORS["bg_primary"], foreground=self.COLORS["text_primary"])
        
        # Label and text styles
        self.style.configure("TLabel", font=("Segoe UI", 11), background=self.COLORS["bg_primary"], foreground=self.COLORS["text_primary"])
        
        # Button styles
        self.style.configure("TButton", font=("Segoe UI", 10), background=self.COLORS["accent"], foreground=self.COLORS["bg_secondary"])
        
        # Action button style
        self.style.configure("Action.TButton", background=self.COLORS["accent"], foreground="white")
        
        # Danger button style
        self.style.configure("Danger.TButton", background=self.COLORS["danger"], foreground="white")
        
        # Icon button style
        self.style.configure("Icon.TButton", font=("Segoe UI", 14))
        
        # API key
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.api = None
        
        # Create main container
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize variables
        self.current_conversation = []
        self.is_api_running = False
        
        # Initialize voice interaction
        self.voice_interaction = None
        self.voice_active = tk.BooleanVar(value=False)
        
        # Create top frame for API key input
        self.create_api_frame()
        
        # Create middle frame for chat display
        self.create_chat_frame()
        
        # Create bottom frame for user input
        self.create_input_frame()
        
        # Create log viewer
        self.create_log_frame()
        
        # Load API key
        self.load_api_key()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize the voice interaction system
        self.initialize_voice_interaction()
        
    def create_api_frame(self):
        """Create the frame for API key input."""
        # Create a card-like container for the API settings
        api_container = ttk.LabelFrame(self.main_frame, text="API Configuration", padding=self.PADDING["medium"])
        api_container.pack(fill=tk.X, pady=self.PADDING["medium"])
        
        # First row for API key
        api_frame = ttk.Frame(api_container)
        api_frame.pack(fill=tk.X, pady=self.PADDING["small"])
        
        # Use grid for better layout
        api_frame.columnconfigure(1, weight=1)
        
        ttk.Label(api_frame, text="Anthropic API Key:").grid(row=0, column=0, padx=self.PADDING["small"], sticky=tk.W)
        
        # API key input with modern styling
        self.api_key_var = tk.StringVar(value=self.api_key)
        key_input_frame = ttk.Frame(api_frame)
        key_input_frame.grid(row=0, column=1, padx=self.PADDING["small"], sticky=tk.EW)
        
        self.api_key_entry = ttk.Entry(key_input_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_check = ttk.Checkbutton(
            key_input_frame, 
            text="Show", 
            variable=self.show_key_var, 
            command=self.toggle_api_key_visibility
        )
        self.show_key_check.pack(side=tk.LEFT, padx=self.PADDING["small"])
        
        self.save_key_button = ttk.Button(
            api_frame, 
            text="Save Key", 
            style="Action.TButton",
            command=self.save_api_key
        )
        self.save_key_button.grid(row=0, column=2, padx=self.PADDING["small"])
        
        # Second row for settings
        settings_frame = ttk.Frame(api_container)
        settings_frame.pack(fill=tk.X, pady=self.PADDING["small"])
        
        # Security level in its own frame
        security_frame = ttk.LabelFrame(settings_frame, text="Security", padding=self.PADDING["small"])
        security_frame.pack(side=tk.LEFT, fill=tk.Y, padx=self.PADDING["small"])
        
        self.security_var = tk.StringVar(value="Medium")
        security_combo = ttk.Combobox(
            security_frame, 
            textvariable=self.security_var,
            values=["Low", "Medium", "High"],
            width=10,
            state="readonly"
        )
        security_combo.pack(side=tk.LEFT, padx=self.PADDING["small"])
        
        # Logging options in its own frame
        logging_frame = ttk.LabelFrame(settings_frame, text="Logging", padding=self.PADDING["small"])
        logging_frame.pack(side=tk.LEFT, fill=tk.Y, padx=self.PADDING["small"])
        
        self.logging_var = tk.BooleanVar(value=True)
        logging_check = ttk.Checkbutton(
            logging_frame, 
            text="Enabled", 
            variable=self.logging_var
        )
        logging_check.pack(side=tk.LEFT, padx=self.PADDING["small"])
        
        # Add view logs button
        view_logs_button = ttk.Button(
            logging_frame,
            text="View Logs",
            command=self.show_log_window
        )
        view_logs_button.pack(side=tk.LEFT, padx=self.PADDING["small"])
        
        # Dark mode toggle in its own frame
        theme_frame = ttk.LabelFrame(settings_frame, text="Theme", padding=self.PADDING["small"])
        theme_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=self.PADDING["small"])
        
        self.dark_mode = tk.BooleanVar(value=False)
        dark_mode_toggle = ttk.Checkbutton(
            theme_frame,
            text="Dark Mode",
            variable=self.dark_mode,
            command=self.toggle_dark_mode
        )
        dark_mode_toggle.pack(side=tk.RIGHT, padx=self.PADDING["small"])
        
    def create_chat_frame(self):
        """Create the frame for chat display."""
        chat_frame = ttk.Frame(self.main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=self.PADDING["medium"])
        
        # Create paned window with styled separator
        self.paned_window = ttk.PanedWindow(chat_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Chat text area frame (left side) with card-like appearance
        self.chat_text_frame = ttk.LabelFrame(self.paned_window, text="Conversation", padding=self.PADDING["small"])
        self.paned_window.add(self.chat_text_frame, weight=60)
        
        # Chat display with modern styling
        chat_container = ttk.Frame(self.chat_text_frame)
        chat_container.pack(fill=tk.BOTH, expand=True, padx=self.PADDING["small"], pady=self.PADDING["small"])
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_container, 
            wrap=tk.WORD, 
            font=("Segoe UI", 11), 
            bg=self.COLORS["bg_secondary"],
            fg=self.COLORS["text_primary"],
            bd=0,  # No border
            padx=self.PADDING["medium"], 
            pady=self.PADDING["medium"]
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Screenshot display frame (right side) with card-like appearance
        self.screenshot_frame = ttk.LabelFrame(self.paned_window, text="Screen View", padding=self.PADDING["small"])
        self.paned_window.add(self.screenshot_frame, weight=40)
        
        # Screenshot display
        screenshot_container = ttk.Frame(self.screenshot_frame, padding=self.PADDING["small"])
        screenshot_container.pack(fill=tk.BOTH, expand=True)
        
        self.screenshot_label = ttk.Label(screenshot_container, background=self.COLORS["bg_secondary"])
        self.screenshot_label.pack(fill=tk.BOTH, expand=True)
        
        # Status bar with modern styling
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, before=chat_frame)
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            status_frame, 
            textvariable=self.status_var, 
            background=self.COLORS["bg_secondary"],
            foreground=self.COLORS["text_secondary"],
            padding=(self.PADDING["medium"], self.PADDING["small"]),
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # Add a space for processing indicator
        self.processing_frame = ttk.Frame(status_frame)
        self.processing_frame.pack(side=tk.RIGHT, padx=self.PADDING["medium"])
        
    def create_input_frame(self):
        """Create the frame for user input."""
        input_frame = ttk.LabelFrame(self.main_frame, text="Message Input", padding=self.PADDING["small"])
        input_frame.pack(fill=tk.X, pady=self.PADDING["medium"])
        
        # User input text area with modern styling
        input_container = ttk.Frame(input_frame, padding=self.PADDING["small"])
        input_container.pack(fill=tk.X, expand=True)
        
        self.user_input = scrolledtext.ScrolledText(
            input_container, 
            wrap=tk.WORD, 
            height=4, 
            font=("Segoe UI", 11),
            bg=self.COLORS["bg_secondary"],
            fg=self.COLORS["text_primary"],
            padx=self.PADDING["medium"],
            pady=self.PADDING["medium"]
        )
        self.user_input.pack(fill=tk.X, pady=self.PADDING["small"])
        self.user_input.bind("<Control-Return>", self.send_message)
        
        # Modern placeholder text
        self.user_input.insert(tk.END, "Type your message here or use voice input...")
        self.user_input.bind("<FocusIn>", self._clear_placeholder)
        
        # Buttons frame
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=self.PADDING["small"])
        
        # Voice interaction controls in their own container
        voice_controls = ttk.LabelFrame(button_frame, text="Voice Controls", padding=self.PADDING["small"])
        voice_controls.pack(side=tk.LEFT, fill=tk.Y, padx=self.PADDING["small"])
        
        # Voice interaction toggle with icon
        self.voice_toggle = ttk.Checkbutton(
            voice_controls,
            text="Continuous Listening",
            variable=self.voice_active,
            command=self.toggle_voice_interaction
        )
        self.voice_toggle.pack(side=tk.LEFT, padx=self.PADDING["small"])
        
        # Microphone button with icon
        self.mic_button = ttk.Button(
            voice_controls,
            text="🎤",
            width=3,
            style="Icon.TButton",
            command=self.start_listening_once
        )
        self.mic_button.pack(side=tk.LEFT, padx=self.PADDING["small"])
        self._create_tooltip(self.mic_button, "Start voice recognition")
        
        # Action buttons container
        action_buttons = ttk.Frame(button_frame)
        action_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=self.PADDING["small"])
        
        # Terminate button with danger style
        self.terminate_button = ttk.Button(
            action_buttons, 
            text="Terminate",
            width=10,
            style="Danger.TButton",
            command=self.terminate_actions,
            state=tk.DISABLED
        )
        self.terminate_button.pack(side=tk.RIGHT, padx=self.PADDING["small"])
        self._create_tooltip(self.terminate_button, "Stop current actions")
        
        # Clear button
        self.clear_button = ttk.Button(
            action_buttons, 
            text="Clear",
            width=8,
            command=self.clear_chat
        )
        self.clear_button.pack(side=tk.RIGHT, padx=self.PADDING["small"])
        self._create_tooltip(self.clear_button, "Clear conversation history")
        
        # Send button with action style
        self.send_button = ttk.Button(
            action_buttons, 
            text="Send",
            width=8,
            style="Action.TButton",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, padx=self.PADDING["small"])
        self._create_tooltip(self.send_button, "Send message (Ctrl+Enter)")
        
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def enter(event):
            x = y = 0
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create tooltip window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(
                self.tooltip, 
                text=text, 
                background=self.COLORS["text_primary"], 
                foreground=self.COLORS["bg_secondary"],
                relief="solid", 
                borderwidth=1, 
                padding=(self.PADDING["small"], self.PADDING["small"])
            )
            label.pack()
            
        def leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
        
    def _clear_placeholder(self, event):
        """Clear placeholder text when input is focused."""
        if self.user_input.get("1.0", tk.END).strip() == "Type your message here or use voice input...":
            self.user_input.delete("1.0", tk.END)
        
    def create_log_frame(self):
        """Create a hidden frame for logs."""
        self.log_window = None
        
    def show_log_window(self):
        """Show the log window."""
        if self.log_window is None or not self.log_window.winfo_exists():
            self.log_window = tk.Toplevel(self.root)
            self.log_window.title("Action Logs")
            self.log_window.geometry("800x600")
            
            log_display = scrolledtext.ScrolledText(
                self.log_window, 
                wrap=tk.WORD, 
                font=("Consolas", 10), 
                bg="#ffffff"
            )
            log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Load logs
            try:
                with open("computer_use_log.txt", "r") as f:
                    log_content = f.read()
                log_display.insert(tk.END, log_content)
            except FileNotFoundError:
                log_display.insert(tk.END, "No logs found.")
                
            log_display.config(state=tk.DISABLED)
            
            # Refresh button
            refresh_button = ttk.Button(
                self.log_window, 
                text="Refresh", 
                command=lambda: self.show_log_window()
            )
            refresh_button.pack(side=tk.RIGHT, padx=10, pady=10)
        else:
            self.log_window.lift()
            
    def toggle_api_key_visibility(self):
        """Toggle visibility of the API key."""
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
            
    def save_api_key(self):
        """Save the API key to a config file."""
        key = self.api_key_var.get().strip()
        if not key:
            messagebox.showerror("Error", "API key cannot be empty.")
            return
            
        try:
            os.makedirs("config", exist_ok=True)
            with open("config/api_key.txt", "w") as f:
                f.write(key)
            self.api_key = key
            messagebox.showinfo("Success", "API key saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API key: {str(e)}")
            
    def load_api_key(self):
        """Load the API key from a config file."""
        try:
            with open("config/api_key.txt", "r") as f:
                key = f.read().strip()
            if key:
                self.api_key = key
                self.api_key_var.set(key)
        except FileNotFoundError:
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load API key: {str(e)}")
            
    def append_to_chat(self, message, sender="assistant"):
        """Append a message to the chat display with a bubble style."""
        self.chat_display.config(state=tk.NORMAL)
        
        # Insert separator if not the first message
        if self.chat_display.index("end-1c") != "1.0":
            self.chat_display.insert(tk.END, "\n", "separator")
        
        # Insert timestamp
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"{timestamp} ", "timestamp")
        
        # Format based on sender with bubble-like appearance
        if sender == "user":
            self.chat_display.insert(tk.END, "You\n", "user_name")
            self.chat_display.insert(tk.END, f"{message}\n", "user_bubble")
        elif sender == "assistant":
            self.chat_display.insert(tk.END, "Claude\n", "assistant_name")
            self.chat_display.insert(tk.END, f"{message}\n", "assistant_bubble")
        elif sender == "tool":
            self.chat_display.insert(tk.END, "Tool Output\n", "tool_name")
            self.chat_display.insert(tk.END, f"{message}\n", "tool_bubble")
        elif sender == "error":
            self.chat_display.insert(tk.END, "Error\n", "error_name")
            self.chat_display.insert(tk.END, f"{message}\n", "error_bubble")
        elif sender == "system":
            self.chat_display.insert(tk.END, "System\n", "system_name")
            self.chat_display.insert(tk.END, f"{message}\n", "system_bubble")
            
        # Configure name tags
        self.chat_display.tag_configure("user_name", 
                                       font=("Segoe UI", 9, "bold"), 
                                       foreground=self.COLORS["accent"],
                                       spacing1=5)
        
        self.chat_display.tag_configure("assistant_name", 
                                       font=("Segoe UI", 9, "bold"), 
                                       foreground=self.COLORS["success"],
                                       spacing1=5)
        
        self.chat_display.tag_configure("tool_name", 
                                       font=("Segoe UI", 9, "bold"), 
                                       foreground=self.COLORS["info"],
                                       spacing1=5)
        
        self.chat_display.tag_configure("error_name", 
                                       font=("Segoe UI", 9, "bold"), 
                                       foreground=self.COLORS["danger"],
                                       spacing1=5)
        
        self.chat_display.tag_configure("system_name", 
                                       font=("Segoe UI", 9, "bold"), 
                                       foreground=self.COLORS["text_secondary"],
                                       spacing1=5)
        
        # Configure timestamp tag
        self.chat_display.tag_configure("timestamp", 
                                       font=("Segoe UI", 8), 
                                       foreground=self.COLORS["text_secondary"],
                                       spacing1=10)
        
        # Configure bubble tags
        self.chat_display.tag_configure("user_bubble", 
                                       background=self.COLORS["light_accent"],
                                       font=("Segoe UI", 11),
                                       lmargin1=20, lmargin2=20, rmargin=100,
                                       relief="solid", borderwidth=1, 
                                       spacing1=3, spacing3=10)
        
        self.chat_display.tag_configure("assistant_bubble", 
                                       background=self.COLORS["bg_secondary"], 
                                       font=("Segoe UI", 11),
                                       lmargin1=100, lmargin2=100, rmargin=20,
                                       relief="solid", borderwidth=1,
                                       spacing1=3, spacing3=10)
        
        self.chat_display.tag_configure("tool_bubble", 
                                       background=self.COLORS["bg_secondary"], 
                                       font=("Courier New", 10),
                                       lmargin1=40, lmargin2=40, rmargin=40,
                                       relief="solid", borderwidth=1,
                                       spacing1=3, spacing3=10)
        
        self.chat_display.tag_configure("error_bubble", 
                                       background="#ffebee", 
                                       font=("Segoe UI", 11),
                                       foreground=self.COLORS["danger"],
                                       lmargin1=40, lmargin2=40, rmargin=40,
                                       relief="solid", borderwidth=1,
                                       spacing1=3, spacing3=10)
        
        self.chat_display.tag_configure("system_bubble", 
                                       background="#f8f9fa", 
                                       font=("Segoe UI", 10, "italic"),
                                       foreground=self.COLORS["text_secondary"],
                                       lmargin1=40, lmargin2=40, rmargin=40, 
                                       relief="solid", borderwidth=1,
                                       spacing1=3, spacing3=10)
        
        # Scroll to the end
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def display_screenshot(self, base64_image):
        """Display a screenshot from base64 data."""
        try:
            # Convert base64 to image
            image_data = base64.b64decode(base64_image)
            image = Image.open(BytesIO(image_data))
            
            # Resize to fit the frame
            frame_width = self.screenshot_frame.winfo_width()
            frame_height = self.screenshot_frame.winfo_height()
            
            if frame_width > 50 and frame_height > 50:  # Ensure valid dimensions
                image.thumbnail((frame_width-20, frame_height-20))
                
            # Convert to PhotoImage and display
            photo = ImageTk.PhotoImage(image)
            self.screenshot_label.config(image=photo)
            self.screenshot_label.image = photo  # Keep a reference
            
            # Save the screenshot to the logs directory
            os.makedirs("logs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image.save(f"logs/screenshot_{timestamp}.png")
            
        except Exception as e:
            self.append_to_chat(f"Failed to display screenshot: {str(e)}", "error")
            
    def output_callback(self, content):
        """Callback for handling assistant output."""
        if content["type"] == "text":
            response_text = content["text"]
            self.append_to_chat(response_text, "assistant")
            
            # Process the response with voice interaction if active
            if self.voice_interaction and self.voice_active.get():
                # Use a background thread to avoid blocking the GUI
                threading.Thread(
                    target=self.speak_response_thread, 
                    args=(response_text,),
                    daemon=True
                ).start()
                
        elif content["type"] == "tool_use":
            tool_name = content["name"]
            tool_input_str = json.dumps(content["input"], indent=2)
            self.append_to_chat(f"Using tool: {tool_name}\n{tool_input_str}", "system")
            
            # Update status to show which tool is being used
            self.status_var.set(f"Using {tool_name}...")
    
    def speak_response_thread(self, text):
        """Background thread for speaking a response."""
        try:
            # Create a new asyncio event loop for the background thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Speak the response
            loop.run_until_complete(self.voice_interaction.speak(text))
            
            loop.close()
        except Exception as e:
            self.root.after(0, lambda: self.append_to_chat(f"Error speaking response: {str(e)}", "error"))
            
    def tool_output_callback(self, result, tool_id):
        """Callback for handling tool output."""
        if result.output:
            self.append_to_chat(result.output, "tool")
        if result.error:
            self.append_to_chat(result.error, "error")
        if result.base64_image:
            self.display_screenshot(result.base64_image)
            
    def api_response_callback(self, request, response, error):
        """Callback for handling API responses."""
        if error:
            self.append_to_chat(f"API error: {str(error)}", "error")
            
    def log_action(self, action_type, details):
        """Log actions for security auditing."""
        if not self.logging_var.get():
            return
            
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("computer_use_log.txt", "a") as f:
                f.write(f"{timestamp} | {action_type} | {details}\n")
        except Exception as e:
            self.append_to_chat(f"Failed to log action: {str(e)}", "error")
            
    def send_message(self, event=None):
        """Send a user message to the API."""
        message = self.user_input.get("1.0", tk.END).strip()
        if not message:
            return
            
        # Clear input first for better UX
        self.user_input.delete("1.0", tk.END)
        
        # Send the message
        self.send_message_text(message)
        
    def run_api(self, message):
        """Run the API in a separate thread."""
        async def run_async():
            try:
                await self.api.run_conversation(
                    message,
                    self.output_callback,
                    self.tool_output_callback,
                    self.api_response_callback
                )
            except Exception as e:
                self.root.after(0, lambda: self.append_to_chat(f"Error: {str(e)}", "error"))
            finally:
                self.root.after(0, self.reset_input_state)
                
        asyncio.run(run_async())
        
    def reset_input_state(self):
        """Reset input state after API processing."""
        self.user_input.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        self.terminate_button.config(state=tk.DISABLED)
        self.hide_processing_indicator()
        self.is_api_running = False
        
    def clear_chat(self):
        """Clear the chat display."""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the chat?"):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.screenshot_label.config(image="")
            self.screenshot_label.image = None
            
    def terminate_actions(self):
        """Terminate running actions."""
        if not self.is_api_running:
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to terminate the current operations?"):
            self.append_to_chat("Terminating current operations...", "system")
            # In a real implementation, we would need to add cancellation functionality to the API
            self.log_action("TERMINATED", "User terminated running operations")
            self.reset_input_state()
            
    def initialize_voice_interaction(self):
        """Initialize the voice interaction system."""
        try:
            self.voice_interaction = VoiceInteraction()
            # Set the message handler to send recognized speech to Claude
            self.voice_interaction.set_message_handler(self.handle_voice_message)
            self.append_to_chat("Voice interaction system initialized", "system")
        except Exception as e:
            self.append_to_chat(f"Failed to initialize voice interaction: {str(e)}", "error")
            self.voice_toggle.config(state=tk.DISABLED)
            self.mic_button.config(state=tk.DISABLED)
    
    def toggle_voice_interaction(self):
        """Toggle continuous voice interaction."""
        if not self.voice_interaction:
            self.append_to_chat("Voice interaction system not available", "error")
            self.voice_active.set(False)
            return
            
        if self.voice_active.get():
            self.voice_interaction.start_listening()
            self.append_to_chat("Voice interaction activated. You can speak to Claude.", "system")
            self.status_var.set("Listening...")
        else:
            self.voice_interaction.stop_listening()
            self.append_to_chat("Voice interaction deactivated", "system")
            self.status_var.set("Ready")
    
    def start_listening_once(self):
        """Listen for speech once."""
        if not self.voice_interaction:
            self.append_to_chat("Voice interaction system not available", "error")
            return
            
        # Disable the button while listening
        self.mic_button.config(state=tk.DISABLED)
        self.status_var.set("Listening...")
        
        # Start listening in a background thread
        threading.Thread(target=self.listen_once_thread, daemon=True).start()
    
    def listen_once_thread(self):
        """Background thread for one-time listening."""
        try:
            # Create a new asyncio event loop for the background thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Listen for speech
            speech_text = loop.run_until_complete(self.voice_interaction.listen_once())
            
            # Process recognized speech
            if speech_text:
                # Use after to ensure thread safety with tkinter
                self.root.after(0, lambda: self.handle_voice_message(speech_text))
            else:
                self.root.after(0, lambda: self.append_to_chat("No speech detected", "system"))
                
            loop.close()
        except Exception as e:
            self.root.after(0, lambda: self.append_to_chat(f"Error in speech recognition: {str(e)}", "error"))
        finally:
            # Re-enable the button
            self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set("Ready"))
    
    def handle_voice_message(self, text):
        """Handle a voice message from the user."""
        # Display the recognized text
        self.append_to_chat(f"🎤 {text}", "user")
        
        # Send it to Claude as if it was typed
        self.send_message_text(text)
    
    def send_message_text(self, message):
        """Send a message to the API without getting it from the input field."""
        if not message.strip():
            return
            
        # Disable input while processing
        self.user_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.terminate_button.config(state=tk.NORMAL)
        self.is_api_running = True
        
        # Show the processing indicator
        self.show_processing_indicator()
        
        # Display user message if not already displayed (voice messages are already displayed)
        if not message.startswith("🎤"):
            self.append_to_chat(message, "user")
        
        self.log_action("USER_MESSAGE", message)
        
        # Initialize API if not done yet
        if self.api is None:
            api_key = self.api_key_var.get().strip()
            if not api_key:
                self.append_to_chat("API key is not set. Please enter your Anthropic API key and save it.", "error")
                self.hide_processing_indicator()
                self.reset_input_state()
                return
                
            self.api = ComputerUseAPI(api_key)
            
        # Run the API in a separate thread to avoid blocking the GUI
        threading.Thread(target=self.run_api, args=(message,), daemon=True).start()
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        if self.dark_mode.get():
            # Dark mode colors
            dark_colors = {
                "bg_primary": "#212529",
                "bg_secondary": "#2a2e33",
                "text_primary": "#f8f9fa",
                "text_secondary": "#adb5bd",
                "light_accent": "#343a40"
            }
            
            # Apply dark colors to UI elements
            self.style.configure("TFrame", background=dark_colors["bg_primary"])
            self.style.configure("TLabelframe", background=dark_colors["bg_primary"])
            self.style.configure("TLabelframe.Label", background=dark_colors["bg_primary"], foreground=dark_colors["text_primary"])
            self.style.configure("TLabel", background=dark_colors["bg_primary"], foreground=dark_colors["text_primary"])
            
            # Update chat and input areas
            self.chat_display.config(bg=dark_colors["bg_secondary"], fg=dark_colors["text_primary"])
            self.user_input.config(bg=dark_colors["bg_secondary"], fg=dark_colors["text_primary"])
            self.screenshot_label.config(background=dark_colors["bg_secondary"])
            
            # Update status bar
            self.status_bar.config(background=dark_colors["bg_secondary"], foreground=dark_colors["text_secondary"])
            
            # Reconfigure bubble tags for chat
            self.chat_display.tag_configure("user_bubble", background=dark_colors["light_accent"])
            self.chat_display.tag_configure("assistant_bubble", background="#1e2124")
            self.chat_display.tag_configure("system_bubble", background="#1e2124")
            self.chat_display.tag_configure("tool_bubble", background="#1e2124")
            
            # Update message timestamp color
            self.chat_display.tag_configure("timestamp", foreground=dark_colors["text_secondary"])
        else:
            # Light mode - restore original colors
            self.style.configure("TFrame", background=self.COLORS["bg_primary"])
            self.style.configure("TLabelframe", background=self.COLORS["bg_primary"])
            self.style.configure("TLabelframe.Label", background=self.COLORS["bg_primary"], foreground=self.COLORS["text_primary"])
            self.style.configure("TLabel", background=self.COLORS["bg_primary"], foreground=self.COLORS["text_primary"])
            
            # Restore chat and input areas
            self.chat_display.config(bg=self.COLORS["bg_secondary"], fg=self.COLORS["text_primary"])
            self.user_input.config(bg=self.COLORS["bg_secondary"], fg=self.COLORS["text_primary"])
            self.screenshot_label.config(background=self.COLORS["bg_secondary"])
            
            # Restore status bar
            self.status_bar.config(background=self.COLORS["bg_secondary"], foreground=self.COLORS["text_secondary"])
            
            # Restore bubble tags
            self.chat_display.tag_configure("user_bubble", background=self.COLORS["light_accent"])
            self.chat_display.tag_configure("assistant_bubble", background=self.COLORS["bg_secondary"])
            self.chat_display.tag_configure("system_bubble", background="#f8f9fa")
            self.chat_display.tag_configure("tool_bubble", background=self.COLORS["bg_secondary"])
            
            # Restore message timestamp color
            self.chat_display.tag_configure("timestamp", foreground=self.COLORS["text_secondary"])
    
    def show_processing_indicator(self):
        """Show a visual indicator that processing is happening."""
        self.status_var.set("Processing...")
        
        # Create a progress bar in the processing frame
        self.progress = ttk.Progressbar(
            self.processing_frame,
            mode="indeterminate",
            length=200
        )
        self.progress.pack(fill=tk.X, expand=True)
        self.progress.start(10)
    
    def hide_processing_indicator(self):
        """Hide the processing indicator."""
        if hasattr(self, "progress"):
            self.progress.stop()
            self.progress.destroy()
        self.status_var.set("Ready")
    
    def on_close(self):
        """Handle window close event."""
        if self.is_api_running:
            if not messagebox.askyesno("Confirm", "Operations are still running. Are you sure you want to exit?"):
                return
        
        # Stop voice interaction if active
        if self.voice_interaction and self.voice_active.get():
            self.voice_interaction.stop_listening()
                
        self.root.destroy()
        
    def get_security_settings(self):
        """Get security settings based on selected level."""
        security_level = self.security_var.get()
        
        if security_level == "Low":
            return {
                "require_approval": False,
                "restricted_paths": [],
                "forbidden_commands": []
            }
        elif security_level == "Medium":
            return {
                "require_approval": True,
                "restricted_paths": ["C:\\Windows", "C:\\Program Files"],
                "forbidden_commands": ["format", "del /s", "rmdir /s"]
            }
        else:  # High
            return {
                "require_approval": True,
                "restricted_paths": ["C:\\Windows", "C:\\Program Files", "C:\\Users"],
                "forbidden_commands": ["format", "del", "rmdir", "reg", "taskkill", "shutdown"]
            }

# Main application entry point
def main():
    """Main application entry point."""
    root = tk.Tk()
    app = ComputerUseGUI(root)
    
    # Set app icon if available
    try:
        root.iconbitmap("icon.ico")
    except tk.TclError:
        pass
        
    # Add menu bar
    menubar = tk.Menu(root)
    
    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Save Chat", command=lambda: save_chat(app))
    file_menu.add_command(label="Clear Chat", command=app.clear_chat)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=app.on_close)
    menubar.add_cascade(label="File", menu=file_menu)
    
    # View menu
    view_menu = tk.Menu(menubar, tearoff=0)
    view_menu.add_command(label="View Logs", command=app.show_log_window)
    menubar.add_cascade(label="View", menu=view_menu)
    
    # Voice menu
    voice_menu = tk.Menu(menubar, tearoff=0)
    voice_menu.add_checkbutton(label="Enable Voice Interaction", 
                              variable=app.voice_active,
                              command=app.toggle_voice_interaction)
    voice_menu.add_command(label="Listen Once", command=app.start_listening_once)
    voice_menu.add_separator()
    voice_menu.add_command(label="Voice Settings", 
                          command=lambda: show_voice_settings(root, app))
    menubar.add_cascade(label="Voice", menu=voice_menu)
    
    # Function to show voice settings dialog
    def show_voice_settings(root, app):
        """Show voice settings dialog."""
        settings_window = tk.Toplevel(root)
        settings_window.title("Voice Interaction Settings")
        settings_window.geometry("500x400")
        settings_window.resizable(True, True)
        
        ttk.Label(settings_window, text="Voice Interaction Settings", 
                 font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Speech recognition frame
        sr_frame = ttk.LabelFrame(settings_window, text="Speech Recognition")
        sr_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Model size
        ttk.Label(sr_frame, text="Whisper Model Size:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        model_var = tk.StringVar(value="base")
        model_combo = ttk.Combobox(
            sr_frame, 
            textvariable=model_var,
            values=["tiny", "base", "small", "medium", "large"],
            state="readonly",
            width=15
        )
        model_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(
            sr_frame, 
            text="Apply",
            command=lambda: change_whisper_model(app, model_var.get())
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Text-to-speech frame
        tts_frame = ttk.LabelFrame(settings_window, text="Text-to-Speech")
        tts_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Rate
        ttk.Label(tts_frame, text="Speech Rate:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        rate_var = tk.IntVar(value=180)
        rate_scale = ttk.Scale(
            tts_frame, 
            from_=100, 
            to=300,
            variable=rate_var,
            orient=tk.HORIZONTAL,
            length=200
        )
        rate_scale.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Label(tts_frame, textvariable=rate_var).grid(row=0, column=2, padx=5, pady=5)
        
        # Volume
        ttk.Label(tts_frame, text="Volume:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        volume_var = tk.DoubleVar(value=1.0)
        volume_scale = ttk.Scale(
            tts_frame, 
            from_=0.0, 
            to=1.0,
            variable=volume_var,
            orient=tk.HORIZONTAL,
            length=200
        )
        volume_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        volume_label = ttk.Label(tts_frame)
        volume_label.grid(row=1, column=2, padx=5, pady=5)
        
        # Update volume label
        def update_volume_label(*args):
            volume_label.config(text=f"{volume_var.get():.1f}")
        volume_var.trace_add("write", update_volume_label)
        update_volume_label()
        
        # Get voices button
        ttk.Button(
            tts_frame, 
            text="Get Available Voices",
            command=lambda: get_available_voices(app, settings_window)
        ).grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        
        # Test frame
        test_frame = ttk.LabelFrame(settings_window, text="Test Settings")
        test_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Test text
        ttk.Label(test_frame, text="Test Text:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        test_text = ttk.Entry(test_frame, width=40)
        test_text.insert(0, "This is a test of the voice settings.")
        test_text.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Test button
        ttk.Button(
            test_frame, 
            text="Test Speech",
            command=lambda: test_voice_settings(
                app, 
                test_text.get(),
                rate_var.get(),
                volume_var.get()
            )
        ).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Save button
        ttk.Button(
            settings_window, 
            text="Save Settings",
            command=lambda: save_voice_settings(
                app, 
                model_var.get(),
                rate_var.get(),
                volume_var.get(),
                settings_window
            )
        ).pack(pady=10)
        
        # Function to change Whisper model
        def change_whisper_model(app, model_size):
            if not app.voice_interaction:
                messagebox.showerror("Error", "Voice interaction system not available")
                return
                
            # Use threading to avoid blocking the GUI
            def change_model_thread():
                try:
                    # Create a new asyncio event loop for the background thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Change the model
                    result = loop.run_until_complete(
                        app.voice_interaction.extension_manager.execute_extension(
                            "speech_recognition", 
                            "set_model",
                            model_size=model_size
                        )
                    )
                    
                    loop.close()
                    
                    # Show the result
                    if result and result.get("status") == "success":
                        messagebox.showinfo("Success", f"Changed to {model_size} model")
                    else:
                        error_msg = result.get("message", "Unknown error") if result else "Failed to change model"
                        messagebox.showerror("Error", error_msg)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to change model: {str(e)}")
            
            threading.Thread(target=change_model_thread, daemon=True).start()
        
        # Function to get available voices
        def get_available_voices(app, parent):
            if not app.voice_interaction:
                messagebox.showerror("Error", "Voice interaction system not available")
                return
                
            # Use threading to avoid blocking the GUI
            def get_voices_thread():
                try:
                    # Create a new asyncio event loop for the background thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Get available voices
                    result = loop.run_until_complete(
                        app.voice_interaction.extension_manager.execute_extension(
                            "text_to_speech", 
                            "voices"
                        )
                    )
                    
                    loop.close()
                    
                    # Show the result
                    if result and result.get("status") == "success":
                        show_voices_dialog(parent, result.get("voices", []))
                    else:
                        error_msg = result.get("message", "Unknown error") if result else "Failed to get voices"
                        messagebox.showerror("Error", error_msg)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to get voices: {str(e)}")
            
            threading.Thread(target=get_voices_thread, daemon=True).start()
        
        # Function to show voices dialog
        def show_voices_dialog(parent, voices):
            voices_window = tk.Toplevel(parent)
            voices_window.title("Available Voices")
            voices_window.geometry("600x400")
            
            # Create a treeview
            columns = ("index", "name", "gender", "language")
            tree = ttk.Treeview(voices_window, columns=columns, show="headings")
            
            # Define headings
            tree.heading("index", text="Index")
            tree.heading("name", text="Name")
            tree.heading("gender", text="Gender")
            tree.heading("language", text="Language")
            
            # Define column widths
            tree.column("index", width=50)
            tree.column("name", width=250)
            tree.column("gender", width=100)
            tree.column("language", width=150)
            
            # Add voices to the treeview
            for voice in voices:
                tree.insert("", "end", values=(
                    voice.get("index", ""),
                    voice.get("name", ""),
                    voice.get("gender", ""),
                    ", ".join(voice.get("languages", []))
                ))
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(voices_window, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            
            # Pack the treeview and scrollbar
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Function to test voice settings
        def test_voice_settings(app, text, rate, volume):
            if not app.voice_interaction:
                messagebox.showerror("Error", "Voice interaction system not available")
                return
                
            if not text:
                text = "This is a test of the voice settings."
                
            # Use threading to avoid blocking the GUI
            def test_voice_thread():
                try:
                    # Create a new asyncio event loop for the background thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Speak the test text
                    loop.run_until_complete(
                        app.voice_interaction.extension_manager.execute_extension(
                            "text_to_speech", 
                            "speak",
                            text=text,
                            rate=rate,
                            volume=volume
                        )
                    )
                    
                    loop.close()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to test voice: {str(e)}")
            
            threading.Thread(target=test_voice_thread, daemon=True).start()
        
        # Function to save voice settings
        def save_voice_settings(app, model_size, rate, volume, window):
            if not app.voice_interaction:
                messagebox.showerror("Error", "Voice interaction system not available")
                return
                
            try:
                # Update the voice interaction configuration
                app.voice_interaction.config["speech_recognition"]["model_size"] = model_size
                app.voice_interaction.config["text_to_speech"]["rate"] = rate
                app.voice_interaction.config["text_to_speech"]["volume"] = volume
                
                # Save the configuration to a file
                os.makedirs("config", exist_ok=True)
                with open("config/voice_config.json", "w") as f:
                    json.dump(app.voice_interaction.config, f, indent=2)
                
                messagebox.showinfo("Success", "Voice settings saved successfully")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="About", command=lambda: show_about(root))
    menubar.add_cascade(label="Help", menu=help_menu)
    
    # Set the menu
    root.config(menu=menubar)
    
    # Function to save chat
    def save_chat(app):
        """Save chat to a file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                chat_content = app.chat_display.get("1.0", tk.END)
                with open(file_path, "w") as f:
                    f.write(chat_content)
                messagebox.showinfo("Success", "Chat saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save chat: {str(e)}")
                
    # Function to show about dialog
    def show_about(root):
        """Show about dialog."""
        about_window = tk.Toplevel(root)
        about_window.title("About")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        
        about_text = """
Claude Computer Use API
Version 1.0.0

This application provides a graphical interface for
interacting with Claude's Computer Use capabilities.

Created using the Anthropic API.

Use responsibly and securely.
        """
        
        about_label = ttk.Label(
            about_window, 
            text=about_text, 
            font=("Segoe UI", 11),
            justify=tk.CENTER,
            padding=20
        )
        about_label.pack(fill=tk.BOTH, expand=True)
        
        ok_button = ttk.Button(
            about_window, 
            text="OK", 
            command=about_window.destroy,
            width=10
        )
        ok_button.pack(pady=10)
        
    # Center the window
    window_width = root.winfo_reqwidth()
    window_height = root.winfo_reqheight()
    position_right = int(root.winfo_screenwidth() / 2 - window_width / 2)
    position_down = int(root.winfo_screenheight() / 2 - window_height / 2)
    root.geometry(f"+{position_right}+{position_down}")
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()