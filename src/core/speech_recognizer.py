#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Speech recognition module using OpenAI's Whisper.

This module provides classes for transcribing audio files and handling
real-time audio capture and transcription.
"""

import os
import tempfile
import threading
import time
from typing import Callable, Dict, List, Optional, Union

import numpy as np
import torch
import whisper


class SpeechRecognizer:
    """
    A class for speech recognition using OpenAI's Whisper model.
    
    This class provides methods for transcribing audio files and
    detecting the language of the audio.
    """
    
    def __init__(self, model_size: str = "base", language: Optional[str] = None,
                 device: Optional[str] = None):
        """
        Initialize the SpeechRecognizer.
        
        Args:
            model_size: The size of the Whisper model to use.
                Options: "tiny", "base", "small", "medium", "large", "large-v2".
            language: The language code to use for transcription.
                If None, language will be auto-detected.
            device: The device to use for inference ("cuda", "cpu", etc.).
                If None, will use CUDA if available, otherwise CPU.
        """
        self.model_size = model_size
        self.language = language
        
        # Set device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """
        Load the Whisper model.
        """
        print(f"Loading Whisper model '{self.model_size}' on {self.device}...")
        self.model = whisper.load_model(self.model_size, device=self.device)
        print(f"Model loaded successfully.")
    
    def transcribe_file(self, audio_path: str) -> Dict:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file to transcribe.
            
        Returns:
            A dictionary containing the transcription results.
        """
        options = {}
        if self.language is not None:
            options["language"] = self.language
            
        result = self.model.transcribe(audio_path, **options)
        return result
    
    def transcribe_audio(self, audio_data: np.ndarray, sr: int = 16000) -> Dict:
        """
        Transcribe audio data.
        
        Args:
            audio_data: Audio data as a numpy array.
            sr: Sample rate of the audio data.
            
        Returns:
            A dictionary containing the transcription results.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
            import soundfile as sf
            sf.write(f.name, audio_data, sr)
            return self.transcribe_file(f.name)
    
    def detect_language(self, audio_path: str) -> str:
        """
        Detect the language of an audio file.
        
        Args:
            audio_path: Path to the audio file.
            
        Returns:
            The detected language code.
        """
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(self.device)
        _, probs = self.model.detect_language(mel)
        return max(probs, key=probs.get)
