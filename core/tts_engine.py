import logging
import threading

class TTSEngine:
    """Offline TTS using pyttsx3. Falls back silently if not installed."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.available = False
        self._init_engine()
    
    def _init_engine(self):
        try:
            import comtypes.client
            comtypes.client.gen_dir = None
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 175)
            self.engine.setProperty('volume', 0.9)
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            self.available = True
            self.logger.info("TTS engine initialized.")
        except ImportError:
            self.logger.warning("pyttsx3 not installed — TTS disabled.")
            self.available = False
        except Exception as e:
            self.logger.error(f"TTS init failed: {e}")
            self.available = False
    
    def speak(self, text):
        """Speak text asynchronously (non-blocking)."""
        if not self.available or not self.engine:
            return
        def _run():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                self.logger.error(f"TTS error: {e}")
        threading.Thread(target=_run, daemon=True).start()
