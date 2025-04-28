#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the audio capture component.

This script tests the basic functionality of the AudioCapture class.
"""

import os
import sys
import time

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core import AudioCapture


def test_audio_capture():
    """
    Test the AudioCapture class by recording a short audio sample.
    """
    print("Initializing audio capture...")
    audio_capture = AudioCapture()
    
    # Record duration in seconds
    duration = 5
    
    print(f"Recording audio for {duration} seconds...")
    print("Please speak into your microphone.")
    
    # Capture audio
    audio_data = audio_capture.capture_audio(duration)
    
    print("Recording complete.")
    print(f"Captured {len(audio_data)} samples at {audio_capture.sample_rate} Hz.")
    
    # Save the audio to a file
    output_file = os.path.join(os.path.dirname(__file__), 'sample_audio.wav')
    audio_capture.save_audio(audio_data, output_file)
    
    print(f"Saved audio to {output_file}")
    print("You can use this file for testing the speech recognition component.")


if __name__ == "__main__":
    test_audio_capture()
