import logging
import threading
import subprocess

class TTSEngine:
    """Offline TTS using native Windows PowerShell System.Speech. Exceptionally reliable without COM cache issues."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available = True
        self.logger.info("TTS engine (PowerShell System.Speech) initialized.")
    
    def speak(self, text):
        """Speak text asynchronously (non-blocking)."""
        if not self.available:
            return
            
        def _run():
            try:
                # Escape quotes for PowerShell
                safe_text = text.replace('"', '""').replace("'", "''")
                # Using System.Speech.Synthesis for built-in high quality local TTS
                ps_script = (
                    'Add-Type -AssemblyName System.Speech; '
                    '$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                    '$synth.Rate = 1; '  # Slightly faster rate
                    f'$synth.Speak("{safe_text}"); '
                    '$synth.Dispose()'
                )
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                self.logger.error(f"TTS error: {e}")
                
        threading.Thread(target=_run, daemon=True).start()
