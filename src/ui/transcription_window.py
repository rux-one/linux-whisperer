#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transcription window for Linux Whisperer.

This module provides a window for displaying real-time transcription results.
"""

import os
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QTextCursor, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QToolBar, QStatusBar,
    QComboBox, QCheckBox, QSlider, QFileDialog
)


class TranscriptionWindow(QMainWindow):
    """
    Window for displaying real-time transcription results.
    
    This class provides a window for displaying real-time transcription
    results and controlling the transcription process.
    """
    
    # Signal emitted when the window is closed
    closed = pyqtSignal()
    
    def __init__(self):
        """
        Initialize the transcription window.
        """
        super().__init__()
        
        # Set up the window
        self.setWindowTitle("Linux Whisperer - Transcription")
        self.setMinimumSize(600, 400)
        
        # Try to load the icon from the resources directory
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "resources", "icons", "app_icon.png"
        )
        
        # Check if the icon file exists
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Use a fallback icon
            self.setWindowIcon(QIcon.fromTheme("audio-input-microphone"))
        
        # Set up the central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Set up the layout
        self.layout = QVBoxLayout(self.central_widget)
        
        # Set up the toolbar
        self._setup_toolbar()
        
        # Set up the transcription text edit
        self._setup_transcription_text_edit()
        
        # Set up the status bar
        self._setup_status_bar()
        
        # Set up the control buttons
        self._setup_control_buttons()
    
    def _setup_toolbar(self):
        """
        Set up the toolbar.
        """
        self.toolbar = QToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # Add the clear action
        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self._clear_transcription)
        self.toolbar.addAction(clear_action)
        
        # Add a separator
        self.toolbar.addSeparator()
        
        # Add the copy action
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self._copy_transcription)
        self.toolbar.addAction(copy_action)
        
        # Add the save action
        save_action = QAction("Save", self)
        save_action.triggered.connect(self._save_transcription)
        self.toolbar.addAction(save_action)
        
        # Add a separator
        self.toolbar.addSeparator()
        
        # Add the font size controls
        self.toolbar.addWidget(QLabel("Font Size:"))
        
        font_size_combo = QComboBox()
        font_size_combo.addItems(["Small", "Medium", "Large", "Extra Large"])
        font_size_combo.setCurrentIndex(1)  # Medium by default
        font_size_combo.currentIndexChanged.connect(self._change_font_size)
        self.toolbar.addWidget(font_size_combo)
    
    def _setup_transcription_text_edit(self):
        """
        Set up the transcription text edit.
        """
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setPlaceholderText("Transcription will appear here...")
        
        # Set a monospaced font
        font = QFont("Monospace")
        font.setPointSize(12)
        self.transcription_text.setFont(font)
        
        self.layout.addWidget(self.transcription_text)
    
    def _setup_status_bar(self):
        """
        Set up the status bar.
        """
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add a status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
    
    def _setup_control_buttons(self):
        """
        Set up the control buttons.
        """
        button_layout = QHBoxLayout()
        
        # Add the insert button
        self.insert_button = QPushButton("Insert Text")
        self.insert_button.clicked.connect(self._insert_text)
        button_layout.addWidget(self.insert_button)
        
        # Add the clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_transcription)
        button_layout.addWidget(self.clear_button)
        
        # Add the close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        self.layout.addLayout(button_layout)
    
    def update_transcription(self, text: str):
        """
        Update the transcription text.
        
        Args:
            text: The transcription text.
        """
        self.transcription_text.setPlainText(text)
        
        # Scroll to the bottom
        cursor = self.transcription_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.transcription_text.setTextCursor(cursor)
        
        # Update the status
        self.status_label.setText("Transcribing...")
    
    def _clear_transcription(self):
        """
        Clear the transcription text.
        """
        self.transcription_text.clear()
        self.status_label.setText("Cleared")
    
    def _copy_transcription(self):
        """
        Copy the transcription text to the clipboard.
        """
        self.transcription_text.selectAll()
        self.transcription_text.copy()
        self.status_label.setText("Copied to clipboard")
    
    def _save_transcription(self):
        """
        Save the transcription text to a file.
        """
        from PyQt6.QtWidgets import QFileDialog
        
        # Get the file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Transcription", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(self.transcription_text.toPlainText())
                    
                self.status_label.setText(f"Saved to {file_path}")
            except Exception as e:
                self.status_label.setText(f"Error saving: {e}")
    
    def _insert_text(self):
        """
        Insert the transcription text into the active application.
        """
        # This will be implemented later to integrate with the text injector
        self.status_label.setText("Text insertion not implemented yet")
    
    def _change_font_size(self, index: int):
        """
        Change the font size of the transcription text.
        
        Args:
            index: The index of the selected font size.
        """
        font = self.transcription_text.font()
        
        if index == 0:  # Small
            font.setPointSize(10)
        elif index == 1:  # Medium
            font.setPointSize(12)
        elif index == 2:  # Large
            font.setPointSize(14)
        elif index == 3:  # Extra Large
            font.setPointSize(16)
            
        self.transcription_text.setFont(font)
    
    def closeEvent(self, event):
        """
        Handle the window close event.
        
        Args:
            event: The close event.
        """
        # Emit the closed signal
        self.closed.emit()
        
        # Accept the event
        event.accept()
