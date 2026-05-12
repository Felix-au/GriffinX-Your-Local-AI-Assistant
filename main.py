import logging
import time
import json
import threading
import keyboard
import os

from core.db import DBManager
from core.context import ContextManager
from core.audio import AudioEngine
from core.llm_engine import LLMEngine
from core.executor import CommandExecutor
from core.macro_manager import MacroManager
from core.tts_engine import TTSEngine
from ui.app import UIEngine

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
        
        logger.info("Initializing Audio & LLM Engines...")
        self.audio = AudioEngine(
            model_size=self.config.get("model_paths", {}).get("whisper", "small.en"),
            device=self.config.get("whisper_device", "auto"),
            compute_type=self.config.get("whisper_compute_type", "int8")
        )
        self.llm = LLMEngine(
            model_path=self.config.get("model_paths", {}).get("llm", "models/Qwen_Qwen3-4B-Q4_K_M.gguf")
        )
        
        logger.info("Initializing TTS, Executor & Macro Managers...")
        self.tts = TTSEngine()
        self.executor = CommandExecutor(self.db)
        self.macro_manager = MacroManager(self.db, self.executor)
        
        self.cache_threshold = self.config.get("cache_threshold", 0.80)
        self.recording_stream = None
        self.pending_feedback_id = None
        self.pending_feedback_text = None
        self.pending_feedback_intent = None
        self.pending_feedback_target = None
        self.ui = None

    def start_listening(self):
        if self.audio.is_recording:
            return
        self.ui.set_status("Listening...")
        self.recording_stream = self.audio.record_audio()
        if self.recording_stream is None:
            self.ui.set_status("Idle (Microphone unavailable)")
        
    def stop_listening_and_process(self):
        if not self.audio.is_recording:
            return
        self.ui.set_status("Transcribing...")
        text = self.audio.stop_recording_and_transcribe(self.recording_stream)
        if not text:
            self.ui.set_status("Idle (No speech detected)")
            return
        logger.info(f"User said: {text}")
        self.ui.set_transcript(text)
        self.ui.set_status("Thinking...")
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
            logger.info(f"Cached: '{self.pending_feedback_text}' → {self.pending_feedback_intent}:{self.pending_feedback_target}")
        elif response == "no":
            self.db.update_feedback(self.pending_feedback_id, "incorrect")
            self.ui.set_response("❌ Feedback logged.")
            logger.info(f"Rejected: '{self.pending_feedback_text}'")
            
        self._clear_feedback()
        
        self._clear_feedback()
        self.ui.set_status("Idle")
    
    def _clear_feedback(self):
        self.pending_feedback_id = None
        self.pending_feedback_text = None
        self.pending_feedback_intent = None
        self.pending_feedback_target = None
        
    def process_command(self, user_text):
        # === STEP 1: Check intent cache (80% match) ===
        cached = self.db.find_cached_intent(user_text, self.cache_threshold)
        
        if cached:
            intent, target, matched_text, ratio = cached
            logger.info(f"Cache HIT ({ratio:.0%}): '{user_text}' ≈ '{matched_text}' → {intent}:{target}")
            self.ui.set_status(f"⚡ Cached: {intent}...")
            self.ui.set_response(f"⚡ Cache match ({ratio:.0%}): {intent} → {target}")
            
            # Execute directly — no LLM inference needed
            intent_data = {"intent": intent, "target": target}
        else:
            # === STEP 2: Full LLM inference ===
            logger.info("Cache MISS — running LLM inference...")
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
            
        elif intent == "macro_creation":
            self.ui.set_status("Saving Macro...")
            macro_name = target or "recent_macro"
            success = self.macro_manager.create_macro_from_history(macro_name, user_text, None)
            status = "Created" if success else "Failed to create macro"
            response_msg = f"Macro '{macro_name}': {status}"
            
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
            
        elif intent == "general_query":
            response_msg = intent_data.get('message', '...')
            logger.info(f"LLM Response: {response_msg}")
            
        # Show response
        if response_msg:
            self.ui.set_response(response_msg)
            self.tts.speak(response_msg[:200])
        
        self.ui.add_history(f"✓ {intent}: {target or user_text[:30]}")
        
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
                if not self.audio.is_recording:
                    self.start_listening()
        elif e.event_type == keyboard.KEY_UP:
            if self.audio.is_recording:
                self.stop_listening_and_process()

    def _handle_text_command(self, text):
        """Handle text input from the UI."""
        logger.info(f"User typed: {text}")
        self.ui.set_transcript(text)
        self.ui.set_status("Thinking...")
        threading.Thread(target=self.process_command, args=(text,), daemon=True).start()

    def toggle_listening(self):
        if self.audio.is_recording:
            self.stop_listening_and_process()
        else:
            self.start_listening()

    def quit(self):
        logger.info("Quitting Trixie...")
        keyboard.unhook_all()

    def run(self):
        """Start the keyboard listener and UI."""
        logger.info("Trixie is starting...")
        keyboard.hook_key('caps lock', self.trigger_push_to_talk, suppress=True)
        self.ui = UIEngine(
            toggle_listening_callback=self.toggle_listening,
            quit_callback=self.quit,
            feedback_callback=self._handle_feedback,
            text_command_callback=self._handle_text_command
        )
        self.ui.run()

if __name__ == "__main__":
    app = TrixieApp()
    app.run()
