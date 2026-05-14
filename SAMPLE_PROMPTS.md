# Trixie: Your Local AI Assistant - Intent Classification Sample Prompts

This guide showcases how Trixie's Qwen 3 4B model translates natural language into executable JSON commands.

## 🚀 App Control

### `open_app`
Used to launch any application, file, or URL.
- **Prompt:** "Open Chrome"
- **Output:** `{"intent": "open_app", "target": "chrome"}`
- **Prompt:** "Can you start Spotify for me?"
- **Output:** `{"intent": "open_app", "target": "spotify"}`

### `close_app`
Used to terminate a running process.
- **Prompt:** "Kill Notepad"
- **Output:** `{"intent": "close_app", "target": "notepad"}`
- **Prompt:** "Close the web browser"
- **Output:** `{"intent": "close_app", "target": "chrome"}`

## ⌨️ User Input & Keys

### `string_type`
Used to type text exactly as requested.
- **Prompt:** "Type my name is Felix"
- **Output:** `{"intent": "string_type", "target": "my name is Felix"}`

### `hotkey`
Used to trigger keyboard combinations.
- **Prompt:** "Press Ctrl C"
- **Output:** `{"intent": "hotkey", "target": "ctrl+c"}`
- **Prompt:** "Do a screen recording shortcut"
- **Output:** `{"intent": "hotkey", "target": "win+alt+r"}`

## 📜 Macros

### `macro_creation`
Starts recording a new sequence of actions.
- **Prompt:** "Remember this setup"
- **Output:** `{"intent": "macro_creation", "target": "setup"}`

### `macro_execution`
Replays a previously saved sequence.
- **Prompt:** "Run my setup macro"
- **Output:** `{"intent": "macro_execution", "target": "setup"}`

## 🧠 Intelligence

### `general_query`
Used for chatting, answering questions, or when no system action is required.
- **Prompt:** "What is the capital of Japan?"
- **Output:** `{"intent": "general_query", "message": "The capital of Japan is Tokyo."}`

### `delay`
Pauses execution (useful in macros).
- **Prompt:** "Wait for 5 seconds"
- **Output:** `{"intent": "delay", "target": "5"}`
