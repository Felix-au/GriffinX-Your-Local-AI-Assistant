import keyboard
import threading
import logging
import json

class MacroManager:
    def __init__(self, db_manager, command_executor):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.executor = command_executor
        self.active_hotkeys = {}
        
        self.load_macros_from_db()
        
    def load_macros_from_db(self):
        macros = self.db.get_all_macros()
        for macro in macros:
            hotkey = macro.get("hotkey")
            actions = macro.get("actions")
            name = macro.get("name")
            if hotkey and actions:
                self.register_hotkey(hotkey, actions, name)
                
    def register_hotkey(self, hotkey_str, actions_list, name="unnamed_macro"):
        if hotkey_str in self.active_hotkeys:
            keyboard.remove_hotkey(self.active_hotkeys[hotkey_str])
            
        def trigger_macro():
            self.logger.info(f"Hotkey triggered macro: {name}")
            # Run in a separate thread so it doesn't block keyboard listening
            threading.Thread(target=self.executor.execute_macro, args=(actions_list,), daemon=True).start()
            
        # Try to register the hotkey system-wide
        try:
            hotkey_id = keyboard.add_hotkey(hotkey_str, trigger_macro)
            self.active_hotkeys[hotkey_str] = hotkey_id
            self.logger.info(f"Registered hotkey {hotkey_str} for macro '{name}'")
        except Exception as e:
            self.logger.error(f"Failed to register hotkey {hotkey_str}: {e}")

    def create_macro_from_history(self, name, target_voice_trigger, target_hotkey, num_recent_actions=3):
        """
        Derives a macro from the last N executed actions in history.
        """
        history = self.db.get_recent_history(limit=num_recent_actions)
        actions = []
        for entry in reversed(history):
            try:
                cmd = json.loads(entry['json_command'])
                # Only save actions, ignore queries or macro commands
                if isinstance(cmd, dict) and cmd.get("intent") not in ["general_query", "screen_analysis", "macro_creation"]:
                    actions.append({
                        "action": cmd.get("intent"),
                        "target": cmd.get("target")
                    })
            except Exception:
                pass
                
        if actions:
            self.save_macro(name, target_voice_trigger, target_hotkey, actions)
            return True
        return False
        
    def save_macro(self, name, voice_trigger, hotkey, actions):
        self.db.save_macro(name, voice_trigger, hotkey, actions)
        if hotkey:
            self.register_hotkey(hotkey, actions, name)
        self.logger.info(f"Successfully saved macro '{name}'.")
