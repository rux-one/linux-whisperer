#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System tray application for Linux Whisperer.

This module provides a system tray icon and menu for controlling
the Linux Whisperer application.
"""

import os
import sys
from typing import Callable, Dict, Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMenu, QSystemTrayIcon, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QCheckBox, QMessageBox
)

from .transcription_window import TranscriptionWindow


class SystemTrayApp(QSystemTrayIcon):
    """
    System tray application for Linux Whisperer.
    
    This class provides a system tray icon and menu for controlling
    the Linux Whisperer application.
    """
    
    def __init__(self, app: QApplication):
        """
        Initialize the system tray application.
        
        Args:
            app: The QApplication instance.
        """
        super().__init__()
        
        self.app = app
        self.transcription_window = None
        
        # State
        self.is_listening = False
        self.is_whispering_mode = False
        self.selected_model = "base"
        self.selected_language = None
        
        # Callbacks
        self.on_start_listening = None
        self.on_stop_listening = None
        self.on_toggle_whispering_mode = None
        self.on_change_model = None
        self.on_change_language = None
        self.on_exit = None
        
        # Set up the system tray icon
        self._setup_icon()
        
        # Set up the menu
        self._setup_menu()
        
        # Show the system tray icon
        self.show()
        
        # Show a notification on startup
        self.showMessage(
            "Linux Whisperer",
            "Linux Whisperer is running in the system tray.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
    def _setup_icon(self):
        """
        Set up the system tray icon.
        """
        # Try to load the icon from the resources directory
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "resources", "icons", "tray_icon.png"
        )
        
        # Check if the icon file exists
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # Use a fallback icon
            self.setIcon(QIcon.fromTheme("audio-input-microphone"))
    
    def _setup_menu(self):
        """
        Set up the system tray menu.
        """
        # Create the menu
        menu = QMenu()
        
        # Add the toggle listening action
        self.toggle_listening_action = QAction("Start Listening")
        self.toggle_listening_action.triggered.connect(self._toggle_listening)
        menu.addAction(self.toggle_listening_action)
        
        # Add the toggle whispering mode action
        self.toggle_whispering_action = QAction("Enable Whispering Mode")
        self.toggle_whispering_action.setCheckable(True)
        self.toggle_whispering_action.triggered.connect(self._toggle_whispering_mode)
        menu.addAction(self.toggle_whispering_action)
        
        # Add a separator
        menu.addSeparator()
        
        # Add the show transcription window action
        show_transcription_action = QAction("Show Transcription Window")
        show_transcription_action.triggered.connect(self._show_transcription_window)
        menu.addAction(show_transcription_action)
        
        # Add a separator
        menu.addSeparator()
        
        # Add the settings submenu
        settings_menu = QMenu("Settings")
        
        # Add the model selection submenu
        model_menu = QMenu("Model")
        
        # Add the model options
        model_group = QActionGroup(self.app)
        model_group.setExclusive(True)
        
        for model_name in ["tiny", "base", "small", "medium", "large"]:
            action = QAction(model_name, model_group)
            action.setCheckable(True)
            action.setChecked(model_name == self.selected_model)
            action.triggered.connect(lambda checked, m=model_name: self._change_model(m))
            model_menu.addAction(action)
        
        settings_menu.addMenu(model_menu)
        
        # Add the language selection submenu
        language_menu = QMenu("Language")
        
        # Add the language options
        language_group = QActionGroup(self.app)
        language_group.setExclusive(True)
        
        # Add auto-detect option
        auto_action = QAction("Auto-detect", language_group)
        auto_action.setCheckable(True)
        auto_action.setChecked(self.selected_language is None)
        auto_action.triggered.connect(lambda checked: self._change_language(None))
        language_menu.addAction(auto_action)
        
        # Add common languages
        for lang_code, lang_name in [
            ("en", "English"),
            ("fr", "French"),
            ("de", "German"),
            ("es", "Spanish"),
            ("it", "Italian"),
            ("nl", "Dutch"),
            ("pt", "Portuguese"),
            ("ja", "Japanese"),
            ("zh", "Chinese"),
            ("ru", "Russian")
        ]:
            action = QAction(f"{lang_name} ({lang_code})", language_group)
            action.setCheckable(True)
            action.setChecked(self.selected_language == lang_code)
            action.triggered.connect(lambda checked, l=lang_code: self._change_language(l))
            language_menu.addAction(action)
        
        settings_menu.addMenu(language_menu)
        
        menu.addMenu(settings_menu)
        
        # Add a separator
        menu.addSeparator()
        
        # Add the about action
        about_action = QAction("About")
        about_action.triggered.connect(self._show_about_dialog)
        menu.addAction(about_action)
        
        # Add the exit action
        exit_action = QAction("Exit")
        exit_action.triggered.connect(self._exit_app)
        menu.addAction(exit_action)
        
        # Set the menu
        self.setContextMenu(menu)
    
    def _toggle_listening(self):
        """
        Toggle the listening state.
        """
        self.is_listening = not self.is_listening
        
        if self.is_listening:
            self.toggle_listening_action.setText("Stop Listening")
            
            # Call the callback if available
            if self.on_start_listening is not None:
                self.on_start_listening()
                
            # Show a notification
            self.showMessage(
                "Linux Whisperer",
                "Started listening.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self.toggle_listening_action.setText("Start Listening")
            
            # Call the callback if available
            if self.on_stop_listening is not None:
                self.on_stop_listening()
                
            # Show a notification
            self.showMessage(
                "Linux Whisperer",
                "Stopped listening.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
    
    def _toggle_whispering_mode(self, checked: bool):
        """
        Toggle the whispering mode.
        
        Args:
            checked: Whether the action is checked.
        """
        self.is_whispering_mode = checked
        
        if checked:
            self.toggle_whispering_action.setText("Disable Whispering Mode")
        else:
            self.toggle_whispering_action.setText("Enable Whispering Mode")
        
        # Call the callback if available
        if self.on_toggle_whispering_mode is not None:
            self.on_toggle_whispering_mode(checked)
            
        # Show a notification
        self.showMessage(
            "Linux Whisperer",
            f"Whispering mode {'enabled' if checked else 'disabled'}.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def _change_model(self, model_name: str):
        """
        Change the model.
        
        Args:
            model_name: The name of the model.
        """
        self.selected_model = model_name
        
        # Call the callback if available
        if self.on_change_model is not None:
            self.on_change_model(model_name)
            
        # Show a notification
        self.showMessage(
            "Linux Whisperer",
            f"Changed model to {model_name}.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def _change_language(self, language_code: Optional[str]):
        """
        Change the language.
        
        Args:
            language_code: The language code, or None for auto-detection.
        """
        self.selected_language = language_code
        
        # Call the callback if available
        if self.on_change_language is not None:
            self.on_change_language(language_code)
            
        # Show a notification
        language_name = "auto-detect" if language_code is None else language_code
        self.showMessage(
            "Linux Whisperer",
            f"Changed language to {language_name}.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def _show_transcription_window(self):
        """
        Show the transcription window.
        """
        if self.transcription_window is None:
            self.transcription_window = TranscriptionWindow()
            self.transcription_window.closed.connect(self._on_transcription_window_closed)
        
        self.transcription_window.show()
        self.transcription_window.activateWindow()
    
    def _on_transcription_window_closed(self):
        """
        Handle the transcription window being closed.
        """
        self.transcription_window = None
    
    def _show_about_dialog(self):
        """
        Show the about dialog.
        """
        QMessageBox.about(
            None,
            "About Linux Whisperer",
            "<h3>Linux Whisperer</h3>"
            "<p>An open-source voice dictation and command tool for Linux.</p>"
            "<p>Version: 0.1.0</p>"
            "<p>License: MIT</p>"
            "<p>Based on OpenAI's Whisper for speech recognition.</p>"
        )
    
    def _exit_app(self):
        """
        Exit the application.
        """
        # Call the callback if available
        if self.on_exit is not None:
            self.on_exit()
        
        # Exit the application
        self.app.quit()
    
    def update_transcription(self, text: str):
        """
        Update the transcription text.
        
        Args:
            text: The transcription text.
        """
        if self.transcription_window is not None:
            self.transcription_window.update_transcription(text)
