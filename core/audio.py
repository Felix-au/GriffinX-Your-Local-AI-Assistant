import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
import logging
from pathlib import Path
from core.model_manager import ensure_model


DEFAULT_STT_MODEL = "models/faster-whisper-medium.en"
FALLBACK_STT_MODEL = "Systran/faster-whisper-medium.en"
COMMAND_TRANSCRIPTION_PROMPT = (
    "Trixie voice commands and app names: open Chrome, open Notepad, open File Explorer, "
    "close Chrome, close Notepad, run, type hello world, press enter, shutdown, shut down, "
    "cancel, stop, hello, Trixie."
)

class AudioEngine:
    def __init__(self, model_size=DEFAULT_STT_MODEL, device="auto", compute_type="default"):
        self.logger = logging.getLogger(__name__)
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        
        # Audio recording config
        self.sample_rate = 16000
        self.channels = 1
        self.audio_queue = queue.Queue()
        self.is_recording = False
        
    def load_model(self):
        if not self.model:
            import ctranslate2
            
            # Intelligent fallback for CPU/GPU
            eff_device = self.device
            eff_compute = self.compute_type
            
            if eff_device == "auto":
                eff_device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
            
            if eff_compute == "default":
                eff_compute = "float16" if eff_device == "cuda" else "int8"
                
            model_size = self.model_size
            if model_size == DEFAULT_STT_MODEL and not Path(model_size).exists():
                self.logger.info("Local STT model not found at %s; downloading...", DEFAULT_STT_MODEL)
                downloaded = ensure_model("stt")
                model_size = downloaded or FALLBACK_STT_MODEL

            self.logger.info(f"Loading Whisper model ({model_size}) on {eff_device} ({eff_compute})...")
            try:
                self.model = WhisperModel(model_size, device=eff_device, compute_type=eff_compute)
            except Exception as e:
                self.logger.error(f"Failed to load Whisper model: {e}")
                self.model = None

    def audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            self.logger.warning(status)
        self.audio_queue.put(indata.copy())

    def record_audio(self):
        self.audio_queue = queue.Queue()
        self.logger.info("Starting audio recording...")
        
        try:
            # We start the stream and return it so the caller can stop it.
            stream = sd.InputStream(samplerate=self.sample_rate, 
                                    device=None,
                                    channels=self.channels, 
                                    callback=self.audio_callback,
                                    dtype='float32')
            stream.start()
            self.is_recording = True
            return stream
        except sd.PortAudioError as e:
            self.logger.error(f"Microphone unavailable: {e}")
            self.is_recording = False
            return None
        except Exception as e:
            self.logger.error(f"Failed to start audio recording: {e}")
            self.is_recording = False
            return None
        
    def stop_recording_and_transcribe(self, stream):
        self.is_recording = False
        
        if stream is None:
            self.logger.warning("No active audio stream to stop.")
            return ""
            
        try:
            stream.stop()
            stream.close()
        except Exception as e:
            self.logger.error(f"Error stopping audio stream: {e}")
            
        self.logger.info("Stopped recording. Processing audio...")
        
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
            
        if not audio_data:
            return ""
            
        audio_np = np.concatenate(audio_data, axis=0)
        # flatten the array
        audio_np = audio_np.flatten()
        
        if not self.model:
            self.load_model()
        
        if not self.model:
            self.logger.error("Whisper model not available for transcription.")
            return ""
            
        segments, info = self.model.transcribe(
            audio_np, 
            beam_size=1, 
            vad_filter=True, 
            vad_parameters=dict(min_silence_duration_ms=500),
            initial_prompt=COMMAND_TRANSCRIPTION_PROMPT,
            language="en"
        )
        
        text_parts = []
        self.logger.info("Transcribing...")
        for segment in segments:
            self.logger.info(f"Heard: {segment.text.strip()}")
            text_parts.append(segment.text)
            
        text = " ".join(text_parts).strip()
        self.logger.info(f"Final transcription: {text}")
        return text
