#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command processor module for Linux Whisperer.

This module provides functionality for detecting and executing
voice commands in the transcribed text.
"""

import os
import re
import subprocess
from typing import Callable, Dict, List, Optional, Tuple, Union


class CommandProcessor:
    """
    A class for processing voice commands.
    
    This class provides methods for detecting and executing
    voice commands in the transcribed text.
    """
    
    def __init__(self, commands_file: Optional[str] = None):
        """
        Initialize the CommandProcessor.
        
        Args:
            commands_file: Path to a JSON file containing custom commands.
                If None, only built-in commands will be available.
        """
        self.commands = self._load_default_commands()
        
        if commands_file and os.path.exists(commands_file):
            self._load_custom_commands(commands_file)
            
        # Callbacks
        self.on_command_executed = None
    
    def _load_default_commands(self) -> Dict[str, Dict]:
        """
        Load the default built-in commands.
        
        Returns:
            A dictionary of command patterns and their handlers.
        """
        return {
            # System commands
            r"(?:open|launch|start)\s+(.+)": {
                "handler": self._handle_open_app,
                "description": "Open an application",
                "example": "open firefox"
            },
            r"(?:close|quit|exit)\s+(?:this|current|)\s*(?:app|application|window|)": {
                "handler": self._handle_close_window,
                "description": "Close the current window",
                "example": "close this window"
            },
            
            # Text editing commands
            r"(?:delete|remove)\s+(?:that|last|previous)\s*(?:line|sentence|paragraph|)": {
                "handler": self._handle_delete_text,
                "description": "Delete the last line or sentence",
                "example": "delete that line"
            },
            r"(?:select|highlight)\s+(?:all|everything)": {
                "handler": self._handle_select_all,
                "description": "Select all text",
                "example": "select all"
            },
            
            # Application control
            r"(?:switch|change)\s+(?:to|)\s*(?:next|previous)\s+(?:app|application|window)": {
                "handler": self._handle_switch_window,
                "description": "Switch to the next or previous window",
                "example": "switch to next window"
            },
            
            # System control
            r"(?:increase|decrease|raise|lower)\s+(?:the|)\s*volume": {
                "handler": self._handle_volume_control,
                "description": "Adjust the system volume",
                "example": "increase the volume"
            },
            
            # Linux Whisperer control
            r"(?:stop|pause)\s+(?:listening|recording|dictation)": {
                "handler": self._handle_stop_listening,
                "description": "Stop the dictation",
                "example": "stop listening"
            },
            r"(?:start|resume)\s+(?:listening|recording|dictation)": {
                "handler": self._handle_start_listening,
                "description": "Start the dictation",
                "example": "start listening"
            }
        }
    
    def _load_custom_commands(self, commands_file: str):
        """
        Load custom commands from a JSON file.
        
        Args:
            commands_file: Path to the JSON file containing custom commands.
        """
        import json
        
        try:
            with open(commands_file, 'r') as f:
                custom_commands = json.load(f)
                
            # Merge custom commands with default commands
            for pattern, command in custom_commands.items():
                if "handler" in command and isinstance(command["handler"], str):
                    # Convert string handler to function reference
                    if hasattr(self, command["handler"]):
                        command["handler"] = getattr(self, command["handler"])
                    else:
                        # Create a shell command handler
                        shell_command = command["handler"]
                        command["handler"] = lambda text, match, cmd=shell_command: self._handle_shell_command(cmd, match)
                        
                self.commands[pattern] = command
                
            print(f"Loaded {len(custom_commands)} custom commands")
        except Exception as e:
            print(f"Error loading custom commands: {e}")
    
    def process_text(self, text: str) -> Tuple[bool, str]:
        """
        Process text to detect and execute commands.
        
        Args:
            text: The text to process.
            
        Returns:
            A tuple of (command_executed, remaining_text).
        """
        if not text:
            return False, ""
            
        # Convert to lowercase for better matching
        lower_text = text.lower()
        
        for pattern, command in self.commands.items():
            match = re.search(pattern, lower_text, re.IGNORECASE)
            if match:
                try:
                    # Execute the command handler
                    result = command["handler"](text, match)
                    
                    # Call the callback if available
                    if self.on_command_executed is not None:
                        self.on_command_executed(pattern, match.group(0), result)
                    
                    # Remove the command from the text
                    start, end = match.span()
                    remaining_text = text[:start] + text[end:]
                    
                    return True, remaining_text.strip()
                except Exception as e:
                    print(f"Error executing command: {e}")
        
        return False, text
    
    def get_available_commands(self) -> List[Dict]:
        """
        Get a list of available commands.
        
        Returns:
            A list of command descriptions.
        """
        result = []
        
        for pattern, command in self.commands.items():
            result.append({
                "pattern": pattern,
                "description": command.get("description", "No description"),
                "example": command.get("example", "No example")
            })
        
        return result
    
    # Command handlers
    
    def _handle_open_app(self, text: str, match: re.Match) -> bool:
        """
        Handle the "open app" command.
        
        Args:
            text: The original text.
            match: The regex match object.
            
        Returns:
            True if the command was executed successfully, False otherwise.
        """
        app_name = match.group(1).strip().lower()
        
        try:
            # Try to launch the application
            subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Opened application: {app_name}")
            return True
        except Exception as e:
            print(f"Error opening application: {e}")
            return False
    
    def _handle_close_window(self, text: str, match: re.Match) -> bool:
        """
        Handle the "close window" command.
        
        Args:
            text: The original text.
            match: The regex match object.
            
        Returns:
            True if the command was executed successfully, False otherwise.
        """
        try:
            # Use xdotool to close the active window (X11 only)
            if os.environ.get('DISPLAY'):
                subprocess.run(['xdotool', 'key', 'alt+F4'], check=True)
                print("Closed active window")
                return True
            else:
                print("Close window command only supported on X11")
                return False
        except Exception as e:
            print(f"Error closing window: {e}")
            return False
    
    def _handle_delete_text(self, text: str, match: re.Match) -> bool:
        """
        Handle the "delete text" command.
        
        Args:
            text: The original text.
            match: The regex match object.
            
        Returns:
            True if the command was executed successfully, False otherwise.
        """
        try:
            # Use keyboard shortcuts to delete text
            if os.environ.get('DISPLAY'):
                # Select to the start of the line
                subprocess.run(['xdotool', 'key', 'shift+Home'], check=True)
                # Delete the selection
                subprocess.run(['xdotool', 'key', 'Delete'], check=True)
                print("Deleted text")
                return True
            else:
                print("Delete text command only supported on X11")
                return False
        except Exception as e:
            print(f"Error deleting text: {e}")
            return False
    
    def _handle_select_all(self, text: str, match: re.Match) -> bool:
        """
        Handle the "select all" command.
        
        Args:
            text: The original text.
            match: The regex match object.
            
        Returns:
            True if the command was executed successfully, False otherwise.
        """
        try:
            # Use Ctrl+A to select all text
            if os.environ.get('DISPLAY'):
                subprocess.run(['xdotool', 'key', 'ctrl+a'], check=True)
                print("Selected all text")
                return True
            else:
                print("Select all command only supported on X11")
                return False
        except Exception as e:
            print(f"Error selecting all text: {e}")
            return False
    
    def _handle_switch_window(self, text: str, match: re.Match) -> bool:
        """
        Handle the "switch window" command.
        
        Args:
            text: The original text.
            match: The regex match object.
            
        Returns:
            True if the command was executed successfully, False otherwise.
        """
        try:
            # Use Alt+Tab to switch windows
            if os.environ.get('DISPLAY'):
                if 'previous' in match.group(0).lower():
                    subprocess.run(['xdotool', 'key', 'alt+shift+Tab'], check=True)
                else:
                    subprocess.run(['xdotool', 'key', 'alt+Tab'], check=True)
                print("Switched window")
                return True
            else:
                print("Switch window command only supported on X11")
                return False
        except Exception as e:
            print(f"Error switching window: {e}")
            return False
    
    def _handle_volume_control(self, text: str, match: re.Match) -> bool:
        """
        Handle the "volume control" command.
        
        Args:
            text: The original text.
            match: The regex match object.
            
        Returns:
            True if the command was executed successfully, False otherwise.
        """
        try:
            # Use amixer to control volume
            if 'increase' in match.group(0).lower() or 'raise' in match.group(0).lower():
                subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '5%+'], check=True)
                print("Increased volume")
            else:
                subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '5%-'], check=True)
                print("Decreased volume")
            return True
        except Exception as e:
            print(f"Error controlling volume: {e}")
            return False
    
    def _handle_stop_listening(self, text: str, match: re.Match) -> bool:
        """
        Handle the "stop listening" command.
        
        Args:
            text: The original text.
            match: The regex match object.
            
        Returns:
            True if the command was executed successfully, False otherwise.
        """
        # This will be handled by the main application
        print("Stop listening command detected")
        return True
    
    def _handle_start_listening(self, text: str, match: re.Match) -> bool:
        """
        Handle the "start listening" command.
        
        Args:
            text: The original text.
            match: The regex match object.
            
        Returns:
            True if the command was executed successfully, False otherwise.
        """
        # This will be handled by the main application
        print("Start listening command detected")
        return True
    
    def _handle_shell_command(self, command: str, match: re.Match) -> bool:
        """
        Handle a shell command.
        
        Args:
            command: The shell command to execute.
            match: The regex match object.
            
        Returns:
            True if the command was executed successfully, False otherwise.
        """
        try:
            # Replace placeholders in the command with match groups
            for i, group in enumerate(match.groups()):
                command = command.replace(f"${i+1}", group)
            
            # Execute the shell command
            subprocess.run(command, shell=True, check=True)
            print(f"Executed shell command: {command}")
            return True
        except Exception as e:
            print(f"Error executing shell command: {e}")
            return False
