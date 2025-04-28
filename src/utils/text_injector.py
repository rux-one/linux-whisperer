#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Text injection module for Linux Whisperer.

This module provides functionality for injecting text into active applications
on Linux using various methods (X11, Wayland, etc.).
"""

import os
import subprocess
import time
from typing import Optional


class TextInjector:
    """
    A class for injecting text into active applications.
    
    This class provides methods for inserting text into the active application
    using various methods depending on the display server (X11, Wayland).
    """
    
    def __init__(self):
        """
        Initialize the TextInjector.
        """
        self.display_server = self._detect_display_server()
        self._init_backend()
    
    def _detect_display_server(self) -> str:
        """
        Detect the display server in use (X11 or Wayland).
        
        Returns:
            The name of the display server ('x11', 'wayland', or 'unknown').
        """
        # Check if running under Wayland
        if os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'
        # Check if running under X11
        elif os.environ.get('DISPLAY'):
            return 'x11'
        else:
            return 'unknown'
    
    def _init_backend(self):
        """
        Initialize the appropriate backend based on the display server.
        """
        if self.display_server == 'x11':
            try:
                # Try to import Xlib
                import Xlib.display
                import Xlib.X
                import Xlib.XK
                import Xlib.protocol.event
                
                self.display = Xlib.display.Display()
                self.root = self.display.screen().root
                self._backend = 'xlib'
            except ImportError:
                # Fall back to xdotool
                self._check_command('xdotool')
                self._backend = 'xdotool'
        elif self.display_server == 'wayland':
            # For Wayland, we'll use wtype if available
            if self._check_command('wtype'):
                self._backend = 'wtype'
            else:
                # Fall back to wl-clipboard + keyboard shortcut
                self._check_command('wl-copy')
                self._backend = 'wl-clipboard'
        else:
            raise RuntimeError(f"Unsupported display server: {self.display_server}")
        
        print(f"Using text injection backend: {self._backend} on {self.display_server}")
    
    def _check_command(self, command: str) -> bool:
        """
        Check if a command is available in the system.
        
        Args:
            command: The command to check.
            
        Returns:
            True if the command is available, False otherwise.
        """
        try:
            subprocess.run(['which', command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def inject_text(self, text: str):
        """
        Inject text into the active application.
        
        Args:
            text: The text to inject.
        """
        if not text:
            return
            
        if self._backend == 'xdotool':
            self._inject_with_xdotool(text)
        elif self._backend == 'wtype':
            self._inject_with_wtype(text)
        elif self._backend == 'wl-clipboard':
            self._inject_with_wl_clipboard(text)
        elif self._backend == 'xlib':
            self._inject_with_xlib(text)
    
    def _inject_with_xdotool(self, text: str):
        """
        Inject text using xdotool.
        
        Args:
            text: The text to inject.
        """
        subprocess.run(['xdotool', 'type', '--clearmodifiers', text], check=True)
    
    def _inject_with_wtype(self, text: str):
        """
        Inject text using wtype.
        
        Args:
            text: The text to inject.
        """
        subprocess.run(['wtype', text], check=True)
    
    def _inject_with_wl_clipboard(self, text: str):
        """
        Inject text using wl-clipboard and keyboard shortcut.
        
        Args:
            text: The text to inject.
        """
        # Copy text to clipboard
        subprocess.run(['wl-copy', text], check=True)
        
        # Simulate Ctrl+V to paste
        time.sleep(0.1)  # Small delay to ensure clipboard is updated
        subprocess.run(['wtype', '-k', 'ctrl+v'], check=True)
    
    def _inject_with_xlib(self, text: str):
        """
        Inject text using Xlib.
        
        Args:
            text: The text to inject.
        """
        import Xlib.display
        import Xlib.X
        import Xlib.XK
        import Xlib.protocol.event
        
        # Get the active window
        window = self.display.get_input_focus().focus
        
        # Send each character as a key press event
        for char in text:
            # Convert character to keysym
            keysym = Xlib.XK.string_to_keysym(char)
            if keysym == 0:
                # Handle special characters
                if char == ' ':
                    keysym = Xlib.XK.XK_space
                elif char == '\n':
                    keysym = Xlib.XK.XK_Return
                elif char == '\t':
                    keysym = Xlib.XK.XK_Tab
                else:
                    continue
            
            # Get the keycode
            keycode = self.display.keysym_to_keycode(keysym)
            
            # Send key press event
            event = Xlib.protocol.event.KeyPress(
                time=int(time.time()),
                root=self.root,
                window=window,
                same_screen=1,
                child=Xlib.X.NONE,
                root_x=0, root_y=0, event_x=0, event_y=0,
                state=0,
                detail=keycode
            )
            window.send_event(event, propagate=True)
            
            # Send key release event
            event = Xlib.protocol.event.KeyRelease(
                time=int(time.time()),
                root=self.root,
                window=window,
                same_screen=1,
                child=Xlib.X.NONE,
                root_x=0, root_y=0, event_x=0, event_y=0,
                state=0,
                detail=keycode
            )
            window.send_event(event, propagate=True)
            
            # Flush the display
            self.display.flush()
            
            # Small delay to prevent overwhelming the application
            time.sleep(0.01)
    
    def get_active_application(self) -> Optional[str]:
        """
        Get the name of the active application.
        
        Returns:
            The name of the active application, or None if it cannot be determined.
        """
        if self.display_server == 'x11':
            try:
                output = subprocess.check_output(
                    ['xprop', '-id', '$(xdotool getactivewindow)', 'WM_CLASS'],
                    shell=True, text=True
                )
                if 'WM_CLASS' in output:
                    # Extract application name
                    parts = output.split('"')
                    if len(parts) >= 3:
                        return parts[3]
            except subprocess.CalledProcessError:
                pass
        elif self.display_server == 'wayland':
            # This is more complex on Wayland and depends on the compositor
            # For now, we'll return a placeholder
            return "Unknown (Wayland)"
            
        return None
