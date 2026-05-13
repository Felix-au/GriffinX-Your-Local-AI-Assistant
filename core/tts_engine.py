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
                import io
                import wave
                
                # Use a BytesIO buffer to capture the synthesis as a WAV file
                # This is the most robust way to handle all Piper versions
                with io.BytesIO() as wav_io:
                    with wave.open(wav_io, "wb") as wav_file:
                        # Set WAV params (Piper medium models are 22050Hz, 16-bit, Mono)
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)
                        wav_file.setframerate(self.voice.config.sample_rate)
                        
                        # Synthesize directly into the wav file object
                        self.voice.synthesize(text, wav_file)
                    
                    wav_io.seek(0)
                    # Load the PCM data from the buffer, skipping the 44-byte WAV header
                    audio_bytes = wav_io.read()[44:]
                
                if not audio_bytes:
                    return
                
                # Convert PCM16 to float32 for sounddevice
                audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Play via sounddevice
                sd.play(audio_np, self.voice.config.sample_rate)
                sd.wait()
            except Exception as e:
                self.logger.error(f"Piper TTS error: {e}")
                
        threading.Thread(target=_run, daemon=True).start()
