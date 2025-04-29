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

import threading
import time
from pynput import keyboard

import pyaudio
import numpy as np
from core.streaming_transcriber import StreamingTranscriber

LANGUAGES = [
    (None, "Auto"),
    ("en", "English"),
    ("pl", "Polish"),
    ("es", "Spanish")
]


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

        self._transcribing = False
        self._transcription_buffer = []
        self._audio_devices = []  # List of device dicts
        self._selected_device_index = None
        self._audio_thread = None
        self._audio_stream = None
        self._audio_thread_stop = threading.Event()
        # Language selection
        self.language_combo = QComboBox()
        for code, label in LANGUAGES:
            self.language_combo.addItem(label, code)
        self.language_combo.setCurrentIndex(0)
        # (Add to toolbar in _setup_toolbar)
        # StreamingTranscriber instance for live transcription
        self._transcriber = StreamingTranscriber()
        self._transcriber.on_transcription = self._on_transcription_result
        self._hotkey_listener_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        self._stop_hotkey_listener = threading.Event()
        self._hotkey_listener_thread.start()
        
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

        # Add the audio device selector
        self.toolbar.addWidget(QLabel("Audio Device:"))
        self.device_combo = QComboBox()
        self._populate_audio_devices()
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        self.toolbar.addWidget(self.device_combo)

        # Add language selector
        self.toolbar.addWidget(self.language_combo)

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
        print(f"[DEBUG] update_transcription called with text: '{text}'" )
        
        # Force clear placeholder text first
        self.transcription_text.clear()
        
        # Set the text directly
        self.transcription_text.setPlainText(text)
        
        # Scroll to the bottom
        cursor = self.transcription_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.transcription_text.setTextCursor(cursor)
        
        # Update the status
        self.status_label.setText("Transcribing...")
        
        # Force UI update
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        print(f"[DEBUG] UI updated with text: '{self.transcription_text.toPlainText()}'" )
    
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
        # Stop hotkey listener thread
        self._stop_hotkey_listener.set()
        if self._hotkey_listener_thread.is_alive():
            self._hotkey_listener_thread.join(timeout=1)
        # Emit the closed signal
        self.closed.emit()
        
        # Accept the event
        event.accept()

    def start_transcription(self):
        """
        Start the transcription process (actual audio capture wired up).
        """
        if not self._transcribing:
            self._transcribing = True
            self._audio_thread_stop.clear()

            # Use selected audio device
            if self._selected_device_index is not None and self._audio_devices:
                dev = self._audio_devices[self._selected_device_index]
                msg = f"Using device: [{dev['index']}] {dev['name']} ({dev['maxInputChannels']}ch)"
                device_index = dev['index']
            else:
                msg = "No audio input device selected!"
                device_index = None
            print(msg)
            self.status_label.setText(msg)
            self._transcription_buffer = []
            self.update_transcription("")
            # Start audio capture thread
            self._audio_thread = threading.Thread(target=self._audio_capture_thread, args=(device_index,), daemon=True)
            self._audio_thread.start()

    def stop_transcription(self):
        """
        Stop the transcription process and print the result.
        """
        if self._transcribing:
            self._transcribing = False
            # Stop audio thread and stream
            self._audio_thread_stop.set()
            if self._audio_thread and self._audio_thread.is_alive():
                self._audio_thread.join(timeout=2)
            if self._audio_stream is not None:
                try:
                    self._audio_stream.stop_stream()
                    self._audio_stream.close()
                except Exception:
                    pass
                self._audio_stream = None
            # Stop transcriber
            self._transcriber.stop()
            self.status_label.setText("Transcription stopped.")

    def _populate_audio_devices(self):
        """
        Populate the audio device dropdown with available input devices.
        """
        pa = pyaudio.PyAudio()
        self._audio_devices = []
        self.device_combo.clear()
        default_index = pa.get_default_input_device_info()["index"] if pa.get_device_count() > 0 else None
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if dev["maxInputChannels"] > 0:
                self._audio_devices.append(dev)
                label = f"[{dev['index']}] {dev['name']}"
                self.device_combo.addItem(label)
        # Select default device
        if default_index is not None:
            for idx, dev in enumerate(self._audio_devices):
                if dev["index"] == default_index:
                    self.device_combo.setCurrentIndex(idx)
                    self._selected_device_index = idx
                    break
        elif self._audio_devices:
            self.device_combo.setCurrentIndex(0)
            self._selected_device_index = 0
        else:
            self._selected_device_index = None
        pa.terminate()

    def _on_device_changed(self, idx):
        """
        Handle change in selected audio device.
        """
        if 0 <= idx < len(self._audio_devices):
            self._selected_device_index = idx
        else:
            self._selected_device_index = None

    def _on_transcription_result(self, text, result):
        """
        Callback for StreamingTranscriber results.
        """
        self._invoke_in_main_thread(lambda: self.update_transcription(text))

    def _audio_capture_thread(self, device_index):
        """
        Capture audio from the selected input device and stream to transcriber.
        Buffer audio chunks and send to transcriber when enough for a segment.
        """
        pa = pyaudio.PyAudio()
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            self._audio_stream = stream
            print(f"[Audio] Recording started on device index {device_index}")
            self._transcriber.start()
            audio_buffer = []
            min_samples = 80000  # 5 seconds at 16kHz
            while not self._audio_thread_stop.is_set():
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    audio_buffer.append(audio_np)
                    total_samples = sum(arr.shape[0] for arr in audio_buffer)
                    if total_samples >= min_samples:
                        segment = np.concatenate(audio_buffer)
                        # Guard: only transcribe if segment is 1D, float32, >= 16000 samples, not all zeros, no NaN/Inf
                        has_nan = np.isnan(segment).any()
                        has_inf = np.isinf(segment).any()
                        if (segment.ndim == 1 and segment.dtype == np.float32 and segment.shape[0] >= 16000
                            and not has_nan and not has_inf and not np.allclose(segment, 0)):
                            # Always use auto-detection mode (which works reliably)
                            # Keep UI language dropdown but ignore its value for now
                            target_samples = 80000   # 5 seconds for auto detection
                            print(f"[DEBUG] Using 5s segment with auto language detection")
                            
                            # Ensure segment is EXACTLY the target length (no more, no less)
                            segment = segment[:target_samples]  # Truncate if too long
                            if segment.shape[0] < target_samples:
                                pad_width = target_samples - segment.shape[0]
                                segment = np.pad(segment, (0, pad_width), mode='constant')
                            
                            # Debug: Print segment properties
                            print(f"[DEBUG] FINAL Segment shape: {segment.shape}, dtype: {segment.dtype}, min: {segment.min()}, max: {segment.max()}, mean: {segment.mean()}")
                            has_nan = np.isnan(segment).any()
                            has_inf = np.isinf(segment).any()
                            print(f"[DEBUG] Segment has_nan: {has_nan}, has_inf: {has_inf}")
                            
                            try:
                                # Always use auto-detection (language=None)
                                # This is the only mode that works reliably with short segments
                                self._transcriber.recognizer.language = None
                                result = self._transcriber.recognizer.transcribe_audio(segment, 16000)
                                print(f"[DEBUG] Transcription result: text={result.get('text')}, full={result}")
                                text = result["text"].strip()
                                # Thread-safe approach: use _invoke_in_main_thread
                                print(f"[DEBUG] Got transcription text: {text}")
                                # Create a copy of the text to avoid reference issues
                                final_text = str(text)
                                # Use a proper thread-safe approach
                                self._invoke_in_main_thread(lambda: self.update_transcription(final_text))
                            except Exception as e:
                                print(f"[Transcription] Error: {e}")
                        audio_buffer = []
                except Exception as e:
                    print(f"[Audio] Error reading: {e}")
                    break
            print("[Audio] Recording stopped.")
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"[Audio] Could not start stream: {e}")
        finally:
            pa.terminate()
            self._audio_stream = None

    def _hotkey_listener(self):
        """
        Listen for Ctrl+Alt press/release globally and trigger transcription.
        """
        ctrl_pressed = False
        alt_pressed = False
        active = False
        def on_press(key):
            nonlocal ctrl_pressed, alt_pressed, active
            if self._stop_hotkey_listener.is_set():
                return False
            try:
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    ctrl_pressed = True
                if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                    alt_pressed = True
                if ctrl_pressed and alt_pressed and not active:
                    active = True
                    # Start transcription in GUI thread
                    self._invoke_in_main_thread(self.start_transcription)
            except Exception:
                pass
        def on_release(key):
            nonlocal ctrl_pressed, alt_pressed, active
            if self._stop_hotkey_listener.is_set():
                return False
            try:
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    ctrl_pressed = False
                if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                    alt_pressed = False
                if active and (not ctrl_pressed or not alt_pressed):
                    active = False
                    # Stop transcription in GUI thread
                    self._invoke_in_main_thread(self.stop_transcription)
            except Exception:
                pass
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            while not self._stop_hotkey_listener.is_set():
                time.sleep(0.1)
            listener.stop()

    def _invoke_in_main_thread(self, func):
        # Ensure func is called in the Qt main thread
        from PyQt6.QtCore import QTimer
        print(f"[DEBUG] Scheduling function in main thread")
        QTimer.singleShot(0, func)
