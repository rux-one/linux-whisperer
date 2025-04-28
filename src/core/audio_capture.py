#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Audio capture module for real-time speech recognition.

This module provides classes for capturing audio from the microphone
and processing it for speech recognition.
"""

import threading
import time
import wave
from queue import Queue
from typing import Callable, List, Optional, Tuple

import numpy as np
import pyaudio


class AudioCapture:
    """
    A class for capturing audio from the microphone.
    
    This class provides methods for capturing audio in real-time
    and processing it for speech recognition.
    """
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024,
                 channels: int = 1, format_type: int = pyaudio.paInt16):
        """
        Initialize the AudioCapture.
        
        Args:
            sample_rate: The sample rate to use for audio capture.
            chunk_size: The size of each audio chunk.
            channels: The number of audio channels (1 for mono, 2 for stereo).
            format_type: The audio format type (from pyaudio).
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format_type = format_type
        
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        self._running = False
        self._audio_buffer = np.array([])
    
    def start_stream(self):
        """
        Start the audio stream.
        """
        if self.stream is not None:
            self.stop_stream()
            
        self.stream = self.pyaudio.open(
            format=self.format_type,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        self._running = True
    
    def stop_stream(self):
        """
        Stop the audio stream.
        """
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self._running = False
    
    def capture_audio(self, duration: float) -> np.ndarray:
        """
        Capture audio for a specified duration.
        
        Args:
            duration: The duration to capture audio for, in seconds.
            
        Returns:
            The captured audio as a numpy array.
        """
        if not self._running:
            self.start_stream()
            
        frames = []
        for _ in range(0, int(self.sample_rate / self.chunk_size * duration)):
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            frames.append(data)
        
        # Convert to numpy array
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        audio_data = audio_data.astype(np.float32) / 32768.0  # Normalize to [-1.0, 1.0]
        
        return audio_data
    
    def save_audio(self, audio_data: np.ndarray, filename: str):
        """
        Save audio data to a WAV file.
        
        Args:
            audio_data: The audio data to save.
            filename: The filename to save to.
        """
        # Convert back to int16
        audio_data = (audio_data * 32768.0).astype(np.int16)
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.pyaudio.get_sample_size(self.format_type))
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
    
    def __del__(self):
        """
        Clean up resources.
        """
        self.stop_stream()
        self.pyaudio.terminate()


class StreamingAudioCapture(AudioCapture):
    """
    A class for continuous audio capture with voice activity detection.
    
    This class extends AudioCapture to provide continuous audio capture
    with callbacks for processing the captured audio.
    """
    
    def __init__(self, callback: Callable[[np.ndarray], None], buffer_duration: float = 30.0,
                 **kwargs):
        """
        Initialize the StreamingAudioCapture.
        
        Args:
            callback: A function to call with the captured audio buffer.
            buffer_duration: The duration of the audio buffer, in seconds.
            **kwargs: Additional arguments to pass to AudioCapture.
        """
        super().__init__(**kwargs)
        self.callback = callback
        self.buffer_duration = buffer_duration
        self.buffer_samples = int(self.sample_rate * buffer_duration)
        
        self._audio_buffer = np.zeros(self.buffer_samples, dtype=np.float32)
        self._buffer_lock = threading.Lock()
        self._capture_thread = None
    
    def start_capturing(self, segment_duration: float = 1.0):
        """
        Start capturing audio continuously.
        
        Args:
            segment_duration: The duration of each audio segment to capture.
        """
        if self._capture_thread is not None and self._capture_thread.is_alive():
            return
            
        self._running = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(segment_duration,),
            daemon=True
        )
        self._capture_thread.start()
    
    def stop_capturing(self):
        """
        Stop capturing audio.
        """
        self._running = False
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=1.0)
            self._capture_thread = None
    
    def _capture_loop(self, segment_duration: float):
        """
        The main capture loop.
        
        Args:
            segment_duration: The duration of each audio segment to capture.
        """
        self.start_stream()
        
        try:
            while self._running:
                # Capture audio segment
                audio_segment = self.capture_audio(segment_duration)
                
                # Update buffer
                with self._buffer_lock:
                    # Shift buffer and add new segment
                    segment_samples = len(audio_segment)
                    if segment_samples > 0:
                        self._audio_buffer = np.roll(self._audio_buffer, -segment_samples)
                        self._audio_buffer[-segment_samples:] = audio_segment[-segment_samples:]
                        
                        # Call the callback with the current buffer
                        self.callback(np.copy(self._audio_buffer))
                
                # Small sleep to prevent CPU overuse
                time.sleep(0.01)
        finally:
            self.stop_stream()
