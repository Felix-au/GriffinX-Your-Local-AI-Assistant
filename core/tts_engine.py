import logging
import threading
import os
import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice

class TTSEngine:
    """High-quality local neural TTS using Piper."""
    def __init__(self, model_path="models/en_US-lessac-medium.onnx"):
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        self.voice = None
        self.available = False
        self._init_engine()
    
    def _init_engine(self):
        if not os.path.exists(self.model_path):
            self.logger.warning(f"Piper model not found at {self.model_path}. TTS disabled.")
            return
            
        try:
            # PiperVoice expects the config to be in the same dir with .json extension
            self.voice = PiperVoice.load(self.model_path)
            self.available = True
            self.logger.info("Piper TTS engine initialized (Local Neural).")
        except Exception as e:
            self.logger.error(f"Piper TTS init failed: {e}")
            self.available = False
    
    def speak(self, text):
        """Speak text asynchronously using neural synthesis."""
        if not self.available or not self.voice:
            return
            
        def _run():
            try:
                # Synthesize to raw PCM bytes
                audio_bytes = b""
                for chunk in self.voice.synthesize(text):
                    # Robust handling of different Piper output formats
                    if hasattr(chunk, "audio"):
                        audio_bytes += chunk.audio
                    elif isinstance(chunk, bytes):
                        audio_bytes += chunk
                    else:
                        # Direct attribute access fallback
                        try:
                            audio_bytes += chunk.audio
                        except AttributeError:
                            # Final fallback attempt
                            audio_bytes += bytes(chunk)
                
                # Convert PCM16 to float32 for sounddevice
                audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Play via sounddevice
                sd.play(audio_np, self.voice.config.sample_rate)
                sd.wait()
            except Exception as e:
                self.logger.error(f"Piper TTS error: {e}")
                
        threading.Thread(target=_run, daemon=True).start()
