import logging
import time
import json
import threading
import keyboard
import os
import ctypes

# Tell Windows taskbar to use Trixie's icon instead of Python's
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Trixie.LocalAI.1.0")
except Exception:
    pass

from core.db import DBManager
from core.context import ContextManager
from core.audio import AudioEngine
from core.llm_engine import LLMEngine
from core.executor import CommandExecutor
from core.macro_manager import MacroManager
from core.tts_engine import TTSEngine
from core.system_monitor import SystemMonitor
from core.settings import load_settings, update_setting
from core.startup_manager import enable_startup, disable_startup, is_startup_enabled
from core.model_manager import ModelDownloadSignals, MODEL_REGISTRY, ensure_model
from ui.app import UIEngine
from ui.theme import get_global_stylesheet

# Suppress HF symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger("main")

class TrixieApp:
    def __init__(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                self.config = json.load(f)
        else:
            self.config = {}

        logger.info("Initializing DB & Context...")
        self.db = DBManager(db_path=self.config.get("db_path"))
        self.context = ContextManager(self.db)

        self.cache_threshold = self.config.get("cache_threshold", 0.80)
        self.recording_stream = None
        self.pending_feedback_id = None
        self.pending_feedback_text = None
        self.pending_feedback_intent = None
        self.pending_feedback_target = None
        self.ui = None
        self.dashboard = None
        self.system_monitor = None
        self.settings = load_settings()
        self._current_hotkey = self.settings.get("hotkey", "ctrl+caps lock")

        # Engines will be initialized AFTER models are ensured
        self.audio = None
        self.llm = None
        self.tts = None
        self.executor = CommandExecutor(self.db)
        self.macro_manager = MacroManager(self.db, self.executor)

    # ── Model download in background with dashboard progress ───
    def _download_models_background(self):
        """Download all models in a background thread, updating dashboard cards."""
        signals = ModelDownloadSignals()

        # Wire signals → dashboard model cards
        def _on_started(key, desc):
            self._log_activity(f"⬇️ Downloading {desc}...")
            card = self._card_for_key(key)
            if card:
                card.set_downloading(0)

        def _on_progress(key, downloaded, total):
            if total > 0:
                pct = int(downloaded * 100 / total)
                card = self._card_for_key(key)
                if card:
                    card.set_downloading(pct)

        def _on_finished(key, path):
            self._log_activity(f"✅ {key.upper()} model ready")
            card = self._card_for_key(key)
            if card:
                card.set_ready(path)

        def _on_failed(key, error):
            self._log_activity(f"❌ {key.upper()} download failed: {error}")
            card = self._card_for_key(key)
            if card:
                card.set_failed(error)

        def _on_present(key, path):
            card = self._card_for_key(key)
            if card:
                card.set_ready(path)

        if signals._emitter:
            signals.download_started.connect(_on_started)
            signals.download_progress.connect(_on_progress)
            signals.download_finished.connect(_on_finished)
            signals.download_failed.connect(_on_failed)
            signals.model_already_present.connect(_on_present)

        def _worker():
            # TTS config + model
            self._log_activity("🔍 Checking TTS models...")
            ensure_model("tts_config", signals=signals)
            tts_model_path = ensure_model("tts_model", signals=signals)

            # LLM
            self._log_activity("🔍 Checking LLM model...")
            llm_path = self.config.get("model_paths", {}).get("llm", "models/Qwen_Qwen3-4B-Q4_K_M.gguf")
            if not os.path.exists(llm_path):
                ensure_model("llm", signals=signals)
            else:
                if signals._emitter:
                    signals.model_already_present.emit("llm", llm_path)

            # Now initialize engines (after models are available)
            self._log_activity("🔧 Initializing engines...")
            try:
                self.audio = AudioEngine(
                    model_size=self.config.get("model_paths", {}).get("whisper", "Systran/faster-distil-whisper-large-v3"),
                    device=self.config.get("whisper_device", "auto"),
                    compute_type=self.config.get("whisper_compute_type", "default")
                )
                # Mark STT as ready once AudioEngine initializes
                self.dashboard.card_stt.set_ready("Whisper loaded")
                self._log_activity("✅ STT engine ready")
            except Exception as e:
                logger.error(f"STT init failed: {e}")
                self.dashboard.card_stt.set_failed(str(e))
                self._log_activity(f"❌ STT init failed: {e}")

            try:
                self.llm = LLMEngine(
                    model_path=self.config.get("model_paths", {}).get("llm", "models/Qwen_Qwen3-4B-Q4_K_M.gguf")
                )
                self._log_activity("✅ LLM engine ready")
            except Exception as e:
                logger.error(f"LLM init failed: {e}")
                self._log_activity(f"❌ LLM init failed: {e}")

            try:
                self.tts = TTSEngine(model_path=tts_model_path) if tts_model_path else TTSEngine()
                self._log_activity("✅ TTS engine ready")
            except Exception as e:
                logger.error(f"TTS init failed: {e}")
                self._log_activity(f"❌ TTS init failed: {e}")

            self._log_activity("🚀 All engines initialized")
            if self.dashboard:
                self.dashboard.update_status_bar(
                    f"Trixie is ready  •  Push-to-talk: {self._current_hotkey}"
                )

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def _card_for_key(self, key):
        """Map model registry key to dashboard card."""
        if not self.dashboard:
            return None
        mapping = {
            "stt": self.dashboard.card_stt,
            "llm": self.dashboard.card_llm,
            "tts_model": self.dashboard.card_tts,
            "tts_config": None,  # config doesn't need a card
        }
        return mapping.get(key)

    def start_listening(self):
        if not self.audio or self.audio.is_recording:
            return
        self.ui.set_status("Listening...")
        self._log_activity("🎙️ Listening started")
        self.recording_stream = self.audio.record_audio()
        if self.recording_stream is None:
            self.ui.set_status("Idle (Microphone unavailable)")

    def stop_listening_and_process(self):
        if not self.audio or not self.audio.is_recording:
            return
        self.ui.set_status("Transcribing...")
        text = self.audio.stop_recording_and_transcribe(self.recording_stream)
        if not text:
            self.ui.set_status("Idle (No speech detected)")
            return
        logger.info(f"User said: {text}")
        self.ui.set_transcript(text)
        self.ui.set_status("Thinking...")
        self._log_activity(f"📝 Transcribed: {text}")
        threading.Thread(target=self.process_command, args=(text,), daemon=True).start()

    def _handle_feedback(self, response):
        """Handle user's yes/no feedback from UI buttons."""
        if self.pending_feedback_id is None:
            return

        self.ui.hide_feedback_buttons()

        if response == "yes":
            self.db.update_feedback(self.pending_feedback_id, "correct")
            self.db.cache_intent(
                self.pending_feedback_text,
                self.pending_feedback_intent,
                self.pending_feedback_target
            )
            self.ui.set_response("✅ Saved to cache.")
            self._log_activity(f"✅ Feedback: correct — cached '{self.pending_feedback_text}'")
            logger.info(f"Cached: '{self.pending_feedback_text}' → {self.pending_feedback_intent}:{self.pending_feedback_target}")
        elif response == "no":
            self.db.update_feedback(self.pending_feedback_id, "incorrect")
            self.ui.set_response("❌ Feedback logged.")
            self._log_activity(f"❌ Feedback: incorrect — '{self.pending_feedback_text}'")
            logger.info(f"Rejected: '{self.pending_feedback_text}'")

        self._clear_feedback()
        self.ui.set_status("Idle")

    def _clear_feedback(self):
        self.pending_feedback_id = None
        self.pending_feedback_text = None
        self.pending_feedback_intent = None
        self.pending_feedback_target = None

    def process_command(self, user_text):
        if not self.llm:
            self.ui.set_response("⏳ LLM is still loading, please wait...")
            self.ui.set_status("Idle")
            return

        # === STEP 1: Check intent cache (80% match) ===
        cached = self.db.find_cached_intent(user_text, self.cache_threshold)

        if cached:
            intent, target, matched_text, ratio = cached
            logger.info(f"Cache HIT ({ratio:.0%}): '{user_text}' ≈ '{matched_text}' → {intent}:{target}")
            self.ui.set_status(f"⚡ Cached: {intent}...")
            self.ui.set_response(f"⚡ Cache match ({ratio:.0%}): {intent} → {target}")
            self._log_activity(f"⚡ Cache HIT ({ratio:.0%}): {intent}:{target}")

            # Execute directly — no LLM inference needed
            intent_data = {"intent": intent, "target": target}
        else:
            # === STEP 2: Full LLM inference ===
            logger.info("Cache MISS — running LLM inference...")
            self._log_activity("🧠 Cache MISS — LLM inference...")
            sys_prompt = self.context.get_system_prompt()
            memory = self.context.get_short_term_memory()
            intent_data = self.llm.get_intent(sys_prompt, user_text, memory)

        intent = intent_data.get("intent", "none")
        target = intent_data.get("target", "")
        logger.info(f"Intent: {intent} (Target: {target})")

        status = "Success"
        executed_actions = None
        response_msg = ""

        if intent in ["open_app", "close_app", "run_script", "string_type", "hotkey", "delay"]:
            self.ui.set_status(f"Executing: {intent}...")
            executed_actions = [{"action": intent, "target": target}]
            status = self.executor.execute(intent, target)
            response_msg = f"{intent}: {target} — {status}"
            self._log_activity(f"⚡ Executed: {intent}:{target} — {status}")

        elif intent == "macro_creation":
            self.ui.set_status("Saving Macro...")
            macro_name = target or "recent_macro"
            success = self.macro_manager.create_macro_from_history(macro_name, user_text, None)
            status = "Created" if success else "Failed to create macro"
            response_msg = f"Macro '{macro_name}': {status}"
            self._log_activity(f"📦 Macro '{macro_name}': {status}")

        elif intent == "macro_execution":
            self.ui.set_status(f"Running Macro: {target}...")
            macros = self.macro_manager.db.get_all_macros()
            match = next((m for m in macros if m.get('name', '').lower() == target.lower()), None)
            if match and match.get('actions'):
                results = self.executor.execute_macro(match['actions'])
                status = "Success" if all(r == "Success" for r in results) else "Partial failure"
                executed_actions = match['actions']
            else:
                status = f"Macro '{target}' not found"
            response_msg = f"Macro '{target}': {status}"
            self._log_activity(f"📦 Macro '{target}': {status}")

        elif intent == "general_query":
            response_msg = intent_data.get('message', '...')
            logger.info(f"LLM Response: {response_msg}")
            self._log_activity(f"💬 Query response sent")

        # Show response
        if response_msg:
            self.ui.set_response(response_msg)
            if self.tts:
                self.tts.speak(response_msg[:200])

        # Log to DB and get the row ID
        row_id = self.db.log_interaction(user_text, intent, intent_data, executed_actions, status)

        # === STEP 3: Ask for feedback (only if NOT from cache) ===
        if not cached and intent != "general_query":
            self.pending_feedback_id = row_id
            self.pending_feedback_text = user_text
            self.pending_feedback_intent = intent
            self.pending_feedback_target = target

            self.ui.set_status("Was that correct?")
            self.ui.show_feedback_buttons()
        else:
            self.ui.set_status("Idle")

    def trigger_push_to_talk(self, e):
        if e.event_type == keyboard.KEY_DOWN:
            if keyboard.is_pressed('ctrl'):
                if not self.audio or not self.audio.is_recording:
                    self.start_listening()
        elif e.event_type == keyboard.KEY_UP:
            if self.audio and self.audio.is_recording:
                self.stop_listening_and_process()

    def _handle_text_command(self, text):
        """Handle text input from the UI."""
        logger.info(f"User typed: {text}")
        self.ui.set_transcript(text)
        self.ui.set_status("Thinking...")
        self._log_activity(f"⌨️ Typed: {text}")
        threading.Thread(target=self.process_command, args=(text,), daemon=True).start()

    def toggle_listening(self):
        if not self.audio:
            return
        if self.audio.is_recording:
            self.stop_listening_and_process()
        else:
            self.start_listening()

    def quit(self):
        logger.info("Quitting Trixie...")
        if self.system_monitor:
            self.system_monitor.stop()
        keyboard.unhook_all()

    def _log_activity(self, message):
        """Send activity message to dashboard if available."""
        if self.dashboard:
            self.dashboard.add_activity(message)

    def _on_setting_changed(self, key, value):
        """Handle dashboard setting changes."""
        update_setting(key, value)
        if key == "start_at_startup":
            if value:
                enable_startup()
            else:
                disable_startup()
        elif key == "hotkey":
            self._rebind_hotkey(value)

    def _rebind_hotkey(self, new_combo: str):
        """Re-register the push-to-talk hotkey."""
        keyboard.unhook_all()
        self._current_hotkey = new_combo
        logger.info(f"Hotkey changed to: {new_combo}")
        self._log_activity(f"🔑 Hotkey changed to: {new_combo}")

        # Parse the combo into modifier + trigger key
        parts = [p.strip().lower() for p in new_combo.split("+")]
        if len(parts) >= 2:
            trigger_key = parts[-1]
            # Re-hook with new trigger key
            keyboard.hook_key(trigger_key, self._hotkey_handler_factory(parts[:-1]), suppress=False)
        
        if self.dashboard:
            self.dashboard.update_status_bar(
                f"Trixie is ready  •  Push-to-talk: {new_combo}"
            )

    def _hotkey_handler_factory(self, modifiers):
        """Create a keyboard handler that checks modifiers."""
        def handler(e):
            if e.event_type == keyboard.KEY_DOWN:
                all_pressed = all(keyboard.is_pressed(m) for m in modifiers)
                if all_pressed and (not self.audio or not self.audio.is_recording):
                    self.start_listening()
            elif e.event_type == keyboard.KEY_UP:
                if self.audio and self.audio.is_recording:
                    self.stop_listening_and_process()
        return handler

    def _show_dashboard(self):
        """Show dashboard window."""
        if self.dashboard:
            self.dashboard.show()
            self.dashboard.raise_()
            self.dashboard.activateWindow()

    def _handle_dashboard_close(self, event):
        """Always minimize to tray on dashboard close."""
        event.ignore()
        self.dashboard.hide()

    def run(self):
        """Start the keyboard listener and UI."""
        logger.info("Trixie is starting...")

        self.ui = UIEngine(
            toggle_listening_callback=self.toggle_listening,
            quit_callback=self.quit,
            feedback_callback=self._handle_feedback,
            text_command_callback=self._handle_text_command
        )

        # Apply global theme stylesheet
        self.ui.app.setStyleSheet(get_global_stylesheet())

        # Set app icon
        from ui.app import _resolve_asset_path
        ico_path = _resolve_asset_path("trixie.ico")
        if os.path.exists(ico_path):
            from PySide6.QtGui import QIcon
            self.ui.app.setWindowIcon(QIcon(ico_path))

        # ── Dashboard ──────────────────────────────────────────
        from ui.dashboard import DashboardWindow
        self.dashboard = DashboardWindow(version="1.0.0")

        # Apply saved settings
        self.dashboard.apply_settings(self.settings)

        # Wire setting changes
        self.dashboard.setting_changed.connect(self._on_setting_changed)

        # Apply startup setting on first run
        if self.settings.get("start_at_startup", True) and not is_startup_enabled():
            enable_startup()

        # Always minimize to tray on close
        self.dashboard.closeEvent = self._handle_dashboard_close

        # Wire dashboard requests — tray icon + overlay logo click
        self.ui.dashboard_requested.connect(self._show_dashboard)
        self.ui.overlay.logo_clicked.connect(self._show_dashboard)

        # ── System Monitor ─────────────────────────────────────
        self.system_monitor = SystemMonitor(interval_ms=1000)
        self.system_monitor.stats_updated.connect(self.dashboard.update_stats)
        self.system_monitor.start()

        # ── Show dashboard FIRST, then download models in background ──
        self.dashboard.show()
        self._log_activity("🚀 Trixie started — downloading models...")
        self.dashboard.update_status_bar("Initializing — downloading models...")

        # Register initial hotkey
        hotkey = self.settings.get("hotkey", "ctrl+caps lock")
        parts = [p.strip().lower() for p in hotkey.split("+")]
        if len(parts) >= 2:
            trigger_key = parts[-1]
            keyboard.hook_key(trigger_key, self._hotkey_handler_factory(parts[:-1]), suppress=False)

        # Start model download in background thread
        self._download_models_background()

        self.ui.run()

if __name__ == "__main__":
    app = TrixieApp()
    app.run()
