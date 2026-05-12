import sqlite3
import json
import os
from datetime import datetime
from difflib import SequenceMatcher

class DBManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "history.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        
        # History table — stores every interaction with feedback
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_input TEXT,
                parsed_intent TEXT,
                json_command TEXT,
                executed_actions TEXT,
                result_status TEXT,
                user_feedback TEXT DEFAULT NULL
            )
        ''')
        
        # Intent cache — verified correct transcription→action mappings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intent_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcription TEXT UNIQUE,
                intent TEXT,
                target TEXT,
                use_count INTEGER DEFAULT 1,
                last_used TEXT
            )
        ''')
        
        # Macros table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS macros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                voice_trigger TEXT,
                hotkey TEXT,
                actions_json TEXT
            )
        ''')
        
        self.conn.commit()

    def log_interaction(self, user_input, intent, command, actions, status):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO history 
            (timestamp, user_input, parsed_intent, json_command, executed_actions, result_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            now, 
            user_input, 
            intent, 
            json.dumps(command) if isinstance(command, dict) else command,
            json.dumps(actions) if isinstance(actions, list) else actions,
            status
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_feedback(self, row_id, feedback):
        """Store user feedback ('correct' or 'incorrect') for an interaction."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE history SET user_feedback = ? WHERE id = ?', (feedback, row_id))
        self.conn.commit()

    def cache_intent(self, transcription, intent, target):
        """Cache a verified-correct transcription→intent mapping."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO intent_cache (transcription, intent, target, use_count, last_used)
            VALUES (?, ?, ?, COALESCE(
                (SELECT use_count + 1 FROM intent_cache WHERE transcription = ?), 1
            ), ?)
        ''', (transcription, intent, target, transcription, now))
        self.conn.commit()

    def find_cached_intent(self, transcription, threshold=0.80):
        """
        Find a cached intent where the transcription matches >= threshold.
        Returns (intent, target, matched_text) or None.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT transcription, intent, target FROM intent_cache')
        
        best_match = None
        best_ratio = 0.0
        
        for row in cursor.fetchall():
            cached_text, intent, target = row
            ratio = SequenceMatcher(None, transcription.lower(), cached_text.lower()).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = (intent, target, cached_text, ratio)
        
        return best_match

    def get_recent_history(self, limit=5):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM history ORDER BY id DESC LIMIT ?', (limit,))
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results

    def save_macro(self, name, voice_trigger, hotkey, actions):
        cursor = self.conn.cursor()
        actions_str = json.dumps(actions) if isinstance(actions, list) else actions
        cursor.execute('''
            INSERT OR REPLACE INTO macros (name, voice_trigger, hotkey, actions_json)
            VALUES (?, ?, ?, ?)
        ''', (name, voice_trigger, hotkey, actions_str))
        self.conn.commit()
        
    def get_all_macros(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM macros')
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            res = dict(zip(columns, row))
            if res.get('actions_json'):
                res['actions'] = json.loads(res['actions_json'])
            results.append(res)
        return results
