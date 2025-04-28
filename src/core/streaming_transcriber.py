#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streaming transcription module for real-time speech recognition.

This module provides a class for continuous speech recognition
using the SpeechRecognizer and AudioCapture classes.
"""

import threading
import time
from typing import Callable, Dict, List, Optional, Union

import numpy as np

from .audio_capture import StreamingAudioCapture
from .speech_recognizer import SpeechRecognizer


class StreamingTranscriber:
    """
    A class for continuous speech recognition.
    
    This class provides methods for continuously capturing audio
    and transcribing it in real-time.
    """
    
    def __init__(self, model_size: str = "base", language: Optional[str] = None,
                 device: Optional[str] = None, buffer_duration: float = 30.0,
                 sample_rate: int = 16000):
        """
        Initialize the StreamingTranscriber.
        
        Args:
            model_size: The size of the Whisper model to use.
            language: The language code to use for transcription.
            device: The device to use for inference.
            buffer_duration: The duration of the audio buffer, in seconds.
            sample_rate: The sample rate to use for audio capture.
        """
        self.recognizer = SpeechRecognizer(model_size, language, device)
        self.sample_rate = sample_rate
        self.buffer_duration = buffer_duration
        
        # Callbacks
        self.on_transcription = None
        self.on_interim_result = None
        
        # State
        self._running = False
        self._transcription_thread = None
        self._audio_capture = None
        self._last_transcription = ""
        self._transcription_lock = threading.Lock()
    
    def start(self, segment_duration: float = 1.0):
        """
        Start the streaming transcription.
        
        Args:
            segment_duration: The duration of each audio segment to capture.
        """
        if self._running:
            return
            
        self._running = True
        
        # Initialize audio capture
        self._audio_capture = StreamingAudioCapture(
            callback=self._process_audio,
            buffer_duration=self.buffer_duration,
            sample_rate=self.sample_rate
        )
        
        # Start capturing audio
        self._audio_capture.start_capturing(segment_duration)
        
        # Start transcription thread
        self._transcription_thread = threading.Thread(
            target=self._transcription_loop,
            daemon=True
        )
        self._transcription_thread.start()
        
        print("Streaming transcription started")
    
    def stop(self):
        """
        Stop the streaming transcription.
        """
        if not self._running:
            return
            
        self._running = False
        
        # Stop audio capture
        if self._audio_capture is not None:
            self._audio_capture.stop_capturing()
            self._audio_capture = None
        
        # Wait for transcription thread to finish
        if self._transcription_thread is not None:
            self._transcription_thread.join(timeout=1.0)
            self._transcription_thread = None
        
        print("Streaming transcription stopped")
    
    def _process_audio(self, audio_buffer: np.ndarray):
        """
        Process the audio buffer.
        
        This method is called by the audio capture when new audio is available.
        It stores the audio buffer for the transcription thread to process.
        
        Args:
            audio_buffer: The audio buffer to process.
        """
        with self._transcription_lock:
            self._current_audio = audio_buffer
            
            # Call interim result callback if available
            if self.on_interim_result is not None:
                # Here we could implement a faster, less accurate interim result
                # For now, we'll just pass the last transcription
                self.on_interim_result(self._last_transcription)
    
    def _transcription_loop(self):
        """
        The main transcription loop.
        
        This method runs in a separate thread and continuously
        transcribes the audio buffer.
        """
        while self._running:
            # Get the current audio buffer
            with self._transcription_lock:
                if not hasattr(self, '_current_audio'):
                    time.sleep(0.1)
                    continue
                    
                audio_buffer = self._current_audio
            
            # Transcribe the audio
            try:
                result = self.recognizer.transcribe_audio(audio_buffer, self.sample_rate)
                text = result["text"].strip()
                
                # Update last transcription
                self._last_transcription = text
                
                # Call transcription callback if available
                if self.on_transcription is not None and text:
                    self.on_transcription(text, result)
            except Exception as e:
                print(f"Error during transcription: {e}")
            
            # Sleep to prevent CPU overuse
            time.sleep(0.1)
