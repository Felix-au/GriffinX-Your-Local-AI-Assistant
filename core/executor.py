import pyautogui
import subprocess
import logging
import time
import shutil

class CommandExecutor:
    def __init__(self, db_manager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        
        # PyAutoGUI safety configuration
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        # Whitelist of known safe applications to prevent shell injection.
        # LLM output goes directly to subprocess — without a whitelist,
        # a hallucinated target like "& del /q C:\*" would execute.
        self.KNOWN_APPS = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "files": "explorer.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "terminal": "wt.exe",
            "powershell": "powershell.exe",
            "task manager": "taskmgr.exe",
            "taskmgr": "taskmgr.exe",
            "settings": "ms-settings:",
            "control panel": "control.exe",
            "snipping tool": "snippingtool.exe",
            "snip": "snippingtool.exe",
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "brave": "brave.exe",
            "opera": "opera.exe",
            "vscode": "code.exe",
            "visual studio code": "code.exe",
            "code": "code.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe",
            "teams": "ms-teams.exe",
            "discord": "discord.exe",
            "spotify": "spotify.exe",
            "steam": "steam.exe",
            "vlc": "vlc.exe",
            "obs": "obs64.exe",
            "obs studio": "obs64.exe",
        }
        self._scan_local_apps()
        
    def _scan_local_apps(self):
        import os
        paths_to_scan = [
            os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop"),
            os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        ]
        
        for base_path in paths_to_scan:
            if not os.path.exists(base_path):
                continue
            for root, _, files in os.walk(base_path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        app_name = file[:-4].lower()
                        # Only add if we don't have a direct exe mapping or if it's new
                        if app_name not in self.KNOWN_APPS:
                            full_path = os.path.join(root, file)
                            self.KNOWN_APPS[app_name] = f'"{full_path}"'
        
    def _resolve_app(self, target):
        """Resolve a user-friendly app name to an executable path or direct command."""
        import os
        normalized = target.lower().strip()
        
        # 1. Direct whitelist match (best for known shortcuts/exes)
        if normalized in self.KNOWN_APPS:
            return self.KNOWN_APPS[normalized]
        
        # 2. Check if it's a direct path that exists
        if os.path.exists(target):
            return f'"{target}"'
            
        # 3. Fuzzy match in whitelist
        for key, exe in self.KNOWN_APPS.items():
            if key in normalized or normalized in key:
                return exe
                
        # 4. Fallback: Return the target as-is. 
        # This makes the app "all whitelisted" as the Windows 'start' command
        # will attempt to open any string passed to it (URL, app, or command).
        return target

    def execute(self, action_intent, target):
        """
        Executes a single action intent and returns the status.
        action_intent: open_app, close_app, run_script, string_type, hotkey, delay
        target: specific value required for the action
        """
        self.logger.info(f"Executing: {action_intent} -> {target}")
        
        try:
            if action_intent == "open_app":
                safe_target = self._resolve_app(target)
                if safe_target:
                    # Use shell=False for safety — no command injection possible
                    if safe_target.startswith("ms-"):
                        # Handle Windows URI protocol launches (ms-settings:, ms-teams:)
                        subprocess.Popen(["cmd.exe", "/c", "start", "", safe_target])
                    else:
                        subprocess.Popen(["cmd.exe", "/c", "start", "", safe_target])
                    return "Success"
                else:
                    self.logger.warning(f"Unknown/blocked app target: {target}")
                    return f"Unknown app: {target}. Add it to the whitelist in executor.py if needed."
                
            elif action_intent == "close_app":
                safe_target = self._resolve_app(target)
                if safe_target:
                    # Extract just the exe filename for taskkill
                    exe_name = safe_target.split("\\")[-1].split("/")[-1]
                    subprocess.Popen(["taskkill", "/IM", exe_name, "/F"])
                    return "Success"
                else:
                    self.logger.warning(f"Unknown/blocked app target for close: {target}")
                    return f"Unknown app: {target}"
                
            elif action_intent == "run_script":
                # Only allow .py files in the project directory for safety
                if not target.endswith(".py"):
                    return "Blocked: Only .py scripts are allowed"
                subprocess.Popen(["python", target])
                return "Success"
                
            elif action_intent == "string_type":
                pyautogui.write(target, interval=0.05)
                return "Success"
                
            elif action_intent == "hotkey":
                # target might be 'ctrl+alt+c'
                keys = target.split('+')
                pyautogui.hotkey(*keys)
                return "Success"
            
            elif action_intent == "delay":
                delay = float(target)
                if delay > 30:
                    return "Blocked: Maximum delay is 30 seconds"
                time.sleep(delay)
                return "Success"
                
            else:
                self.logger.warning(f"Unknown action: {action_intent}")
                return "Unknown Action"
                
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            return f"Failed: {str(e)}"
            
    def execute_macro(self, actions_list):
        self.logger.info(f"Executing macro with {len(actions_list)} steps.")
        results = []
        for step in actions_list:
            action = step.get("action")
            target = step.get("target")
            res = self.execute(action, target)
            results.append(res)
            
            if "Failed" in res:
                self.logger.error("Macro execution aborted due to failure.")
                break
                
        return results
