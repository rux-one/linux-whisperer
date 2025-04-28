#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux Whisperer - An open-source voice dictation and command tool for Linux.

This is the main entry point for the application.
"""

import argparse
import os
import signal
import sys
import time
from typing import Dict, Optional

from core import SpeechRecognizer, StreamingTranscriber


class LinuxWhisperer:
    """
    Main application class for Linux Whisperer.
    """
    
    def __init__(self, model_size: str = "base", language: Optional[str] = None,
                 device: Optional[str] = None):
        """
        Initialize the Linux Whisperer application.
        
        Args:
            model_size: The size of the Whisper model to use.
            language: The language code to use for transcription.
            device: The device to use for inference.
        """
        self.model_size = model_size
        self.language = language
        self.device = device
        
        # Initialize transcriber
        self.transcriber = StreamingTranscriber(
            model_size=model_size,
            language=language,
            device=device
        )
        
        # Set up callbacks
        self.transcriber.on_transcription = self._on_transcription
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """
        Start the application.
        """
        print(f"Starting Linux Whisperer with model '{self.model_size}'")
        print(f"Language: {self.language or 'auto-detect'}")
        print(f"Device: {self.device or 'auto-select'}")
        print("Press Ctrl+C to stop")
        
        # Start transcription
        self.transcriber.start()
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """
        Stop the application.
        """
        print("Stopping Linux Whisperer...")
        self.transcriber.stop()
        print("Stopped")
    
    def _on_transcription(self, text: str, result: Dict):
        """
        Callback for transcription results.
        
        Args:
            text: The transcribed text.
            result: The full transcription result.
        """
        print(f"\nTranscription: {text}")
        
        # Here we would process commands, insert text, etc.
        # For now, we just print the transcription
    
    def _signal_handler(self, sig, frame):
        """
        Handle signals (e.g., Ctrl+C).
        
        Args:
            sig: The signal number.
            frame: The current stack frame.
        """
        self.stop()
        sys.exit(0)


def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Linux Whisperer - Voice dictation and command tool")
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "large-v2"],
        help="The size of the Whisper model to use"
    )
    
    parser.add_argument(
        "--language", "-l",
        type=str,
        default=None,
        help="The language code to use for transcription (e.g., 'en', 'fr', 'de')"
    )
    
    parser.add_argument(
        "--device", "-d",
        type=str,
        default=None,
        help="The device to use for inference (e.g., 'cuda', 'cpu')"
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point.
    """
    args = parse_args()
    
    app = LinuxWhisperer(
        model_size=args.model,
        language=args.language,
        device=args.device
    )
    
    app.start()


if __name__ == "__main__":
    main()
