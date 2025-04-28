#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the speech recognition component.

This script tests the basic functionality of the SpeechRecognizer class.
"""

import os
import sys
import time

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core import SpeechRecognizer


def test_speech_recognizer():
    """
    Test the SpeechRecognizer class with a sample audio file.
    """
    # Create a speech recognizer with the tiny model for faster testing
    recognizer = SpeechRecognizer(model_size="tiny")
    
    # Check if the model was loaded successfully
    assert recognizer.model is not None, "Failed to load Whisper model"
    
    print("Speech recognizer initialized successfully.")
    print(f"Model size: {recognizer.model_size}")
    print(f"Device: {recognizer.device}")
    
    # Test with a sample audio file if available
    sample_file = os.path.join(os.path.dirname(__file__), 'sample_audio.wav')
    
    if os.path.exists(sample_file):
        print(f"\nTranscribing sample audio file: {sample_file}")
        result = recognizer.transcribe_file(sample_file)
        print(f"Transcription: {result['text']}")
    else:
        print(f"\nSample audio file not found: {sample_file}")
        print("Please create a sample audio file for testing.")


if __name__ == "__main__":
    test_speech_recognizer()
