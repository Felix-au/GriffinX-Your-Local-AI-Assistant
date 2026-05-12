# Trixie — Improvement Plan & Recommendations

> **Trixie — Your PC, Your Voice, No Cloud.**

---

## 🏷️ Tagline Candidates

Here are my top picks — ranked by vibe:

| # | Tagline | Tone |
|---|---|---|
| 🥇 | **Trixie — Your PC, Your Voice, No Cloud.** | Clean, confident, privacy-forward |
| 🥈 | **Trixie — Speak. Control. Automate.** | Action-oriented, punchy |
| 🥉 | **Trixie — The AI That Never Phones Home.** | Clever, personality-driven |
| 4 | **Trixie — Local Intelligence, Total Control.** | Professional, enterprise-leaning |
| 5 | **Trixie — Command Your Desktop, Privately.** | Direct and descriptive |
| 6 | **Trixie — No Cloud. No Limits. Just You.** | Bold, aspirational |
| 7 | **Trixie — Your Private Desktop Brain.** | Friendly, approachable |

---

## 🧠 Model Upgrades

### LLM (Intent Classification + Chat)

| Model | Params | GGUF Size (Q4) | Why Upgrade |
|---|---|---|---|
| **Current: Phi-3 Mini** | 3.8B | ~2.2 GB | Decent but older, weaker at structured JSON |
| ⭐ **Phi-4 Mini** | 3.8B | ~2.3 GB | Direct successor — much better reasoning, function calling, structured output. Drop-in replacement. |
| ⭐ **Qwen 3 (4B)** | 4B | ~2.5 GB | Excellent at structured JSON, multilingual, supports tool-calling natively. Best-in-class for its size. |
| **Gemma 3 (4B)** | 4B | ~2.5 GB | Google's latest, very fast, strong instruction following. |
| **Llama 3.2 (3B)** | 3B | ~1.8 GB | Meta's smallest, very efficient, good for simple intent classification. |

> [!TIP]
> **Recommendation**: Switch to **Qwen 3 4B Q4** or **Phi-4 Mini Q4**. Both are near drop-in replacements with dramatically better JSON output reliability. Qwen 3 is the strongest at structured output; Phi-4 has the smoothest migration path since you already use Phi-3's chat template.

### Vision (Screen Understanding)

| Model | Params | GGUF Size (Q4) | Why Upgrade |
|---|---|---|---|
| **Current: MiniCPM-V 2.5** | ~8B | ~5.6 GB total | Works but large, slow, not optimized for UI |
| ⭐ **Gemma 3 4B (Vision)** | 4B | ~2.8 GB + mmproj | Half the size, faster, excellent screen understanding |
| ⭐ **Qwen 3.5-VL (small)** | ~4-7B | ~3-4 GB | King of UI automation — specifically trained for desktop/mobile screen parsing |
| **GLM-4.6V-Flash** | 9B | ~5 GB | Native tool-calling, excellent for agentic screen interaction |
| **Phi-4 Mini Vision** | 3.8B | ~2.3 GB + mmproj | Lightweight, fast, good for basic screen analysis |

> [!TIP]
> **Recommendation**: Switch to **Gemma 3 4B Vision**. Cuts VRAM/RAM in half versus MiniCPM-V while being better at UI understanding. If you want top-tier screen parsing, **Qwen 3.5-VL** is the gold standard but heavier.

### STT (Speech-to-Text)

| Model | Size | Latency | Why Upgrade |
|---|---|---|---|
| **Current: Whisper tiny.en** | ~75 MB | Very fast | Very low accuracy — misrecognizes frequently |
| ⭐ **Moonshine (245M)** | ~245 MB | Ultra-low | Purpose-built for real-time streaming, minimal revision, energy-efficient. Best for push-to-talk. |
| ⭐ **Whisper small.en** | ~461 MB | Moderate | Same ecosystem, massive accuracy jump, simple swap |
| **NVIDIA Parakeet TDT 1.1B** | ~1.1 GB | Very fast | Fastest on Open ASR benchmarks, excellent English |
| **Whisper medium.en** | ~1.5 GB | Slower | Best accuracy in Whisper family for English |

> [!TIP]
> **Recommendation**: Quickest win is **Whisper small.en** — just change one config string and accuracy jumps dramatically. For real-time streaming excellence, **Moonshine** is purpose-built for exactly your push-to-talk use case.

### Combined Upgrade Summary

| Role | Current | Recommended | Size Change | Impact |
|---|---|---|---|---|
| LLM | Phi-3 Mini Q4 (2.2 GB) | Qwen 3 4B Q4 (~2.5 GB) | +0.3 GB | ⬆️⬆️⬆️ JSON reliability, tool-calling |
| Vision | MiniCPM-V 2.5 (5.6 GB) | Gemma 3 4B Vision (~2.8 GB) | **−2.8 GB** | ⬆️⬆️ Speed, ⬆️ accuracy, half the RAM |
| STT | Whisper tiny.en (75 MB) | Whisper small.en (461 MB) | +0.4 GB | ⬆️⬆️⬆️ Accuracy |
| **Total** | **~7.9 GB** | **~5.8 GB** | **−2.1 GB** | Smaller footprint, better everywhere |

---

## 🖥️ UI Improvements

The current UI is a bare system tray icon with a context menu. Here's the vision for a proper UI:

### Phase 1: Floating Overlay Widget (Priority)

```
┌──────────────────────────────────┐
│  ◉ Trixie              ─ □ ✕   │
├──────────────────────────────────┤
│                                  │
│   ╭────────────────────────╮     │
│   │    ◖ ◗  Listening...   │     │  ← Animated mic orb
│   │    ~~~~~~~~████~~~~~   │     │  ← Live waveform
│   ╰────────────────────────╯     │
│                                  │
│   💬 "Open Notepad"              │  ← Transcription bubble
│   ✅ Opened notepad              │  ← Response/status
│                                  │
│   ─────────────────────────────  │
│   🕐 2 min ago: Closed Chrome    │  ← Recent history
│   🕐 5 min ago: Typed "hello"    │
│                                  │
└──────────────────────────────────┘
```

**Key features:**
- **Translucent, always-on-top** floating window (glassmorphism aesthetic)
- **Animated microphone orb** that pulses when listening, shows waveform
- **Transcription + response bubbles** so the user sees what Trixie heard and did
- **Draggable, resizable**, pinnable to screen edge
- **Minimize to tray** (keep current tray as fallback)

### Phase 2: Settings & Macro Editor

- **Settings panel**: Model paths, hotkey config, theme (dark/light), auto-start
- **Macro editor GUI**: View saved macros, edit action sequences, assign hotkeys, test macros
- **History viewer**: Searchable log of all past interactions with intent + result

### Phase 3: Advanced Visual Feedback

- **Toast notifications** with response text (instead of just "status: Idle")
- **TTS feedback** — speak the response back (e.g., via `pyttsx3` or `edge-tts`)
- **Screen analysis overlay** — highlight regions the vision model identified
- **Dark/light theme toggle** with smooth transitions

### UI Tech Recommendation

Keep **PyQt6** — it's the right choice for this project. It gives you:
- Native system tray integration
- Full widget toolkit for complex UIs
- Custom painting for waveform/animations
- Cross-thread signals (already using)
- Good PyInstaller compatibility

---

## 🔧 Code Improvements

### 🔴 Critical Fixes

#### 1. Sanitize Executor Input (Security)
```python
# core/executor.py — whitelist-based app resolution
KNOWN_APPS = {
    "notepad": "notepad.exe",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "calculator": "calc.exe",
    "explorer": "explorer.exe",
    # ... extensible via config.json
}

def execute(self, action_intent, target):
    if action_intent == "open_app":
        safe_target = KNOWN_APPS.get(target.lower())
        if safe_target:
            subprocess.Popen([safe_target])
        else:
            self.logger.warning(f"Unknown app: {target}")
            return f"Unknown app: {target}"
```

#### 2. Fix Dead Vision Context
```python
# core/context.py — inject screen context into prompt
def get_system_prompt(self):
    prompt = "You are Trixie..." # base prompt
    if self.active_screen_context:
        prompt += f"\n\nCurrent screen state:\n{self.active_screen_context}\n"
    return prompt
```

#### 3. Remove DB Singleton
```diff
# core/db.py — line 91
-db = DBManager()
```

#### 4. Pass Config to DBManager
```python
# main.py — pass db_path from config
self.db = DBManager(db_path=self.config.get("db_path"))
```

### 🟡 Feature Gaps

#### 5. Add `macro_execution` Intent Handler
```python
# main.py — in process_command()
elif intent == "macro_execution":
    self.ui.set_status("Running Macro...")
    macros = self.macro_manager.db.get_all_macros()
    match = next((m for m in macros if m['name'] == target), None)
    if match:
        results = self.executor.execute_macro(match['actions'])
        status = "Success" if all(r == "Success" for r in results) else "Partial"
    else:
        status = f"Macro '{target}' not found"
```

#### 6. Add TTS Response for General Queries
```python
# Option A: lightweight, offline
import pyttsx3
engine = pyttsx3.init()
engine.say(response_text)
engine.runAndWait()

# Option B: higher quality, needs internet
# pip install edge-tts
```

#### 7. Better JSON Parsing in LLM Engine
```python
import re

def extract_json(text):
    # Handle nested JSON properly
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
    if match:
        return json.loads(match.group())
    return None
```

### 🟢 Polish

#### 8. Fix PyInstaller Path Separator
```diff
# package.py
-"--add-data=core:core",
-"--add-data=ui:ui",
+"--add-data=core;core",
+"--add-data=ui;ui",
```

#### 9. Error Recovery for Audio
```python
def record_audio(self):
    try:
        stream = sd.InputStream(...)
        stream.start()
        self.is_recording = True
        return stream
    except sd.PortAudioError as e:
        self.logger.error(f"Microphone unavailable: {e}")
        self.is_recording = False
        return None
```

#### 10. Fix README Hotkey Documentation
```diff
-A blue icon will appear in your system tray. **Hold the `Pause/Break` key
+A blue icon will appear in your system tray. **Hold `Ctrl + CapsLock`
```

---

## 📁 Project Structure (Proposed)

```
Trixie/
├── .gitignore              ✅ Created
├── README.md
├── LICENSE
├── config.json
├── requirements.txt
├── install.py
├── download_models.py
├── package.py
├── main.py
├── core/
│   ├── __init__.py         🆕
│   ├── audio.py
│   ├── context.py
│   ├── db.py
│   ├── executor.py
│   ├── llm_engine.py
│   ├── macro_manager.py
│   ├── vision_engine.py
│   └── tts_engine.py       🆕 Text-to-Speech
├── ui/
│   ├── __init__.py          🆕
│   ├── app.py               (system tray, kept as fallback)
│   ├── overlay.py           🆕 Floating widget
│   ├── settings.py          🆕 Settings panel
│   ├── macro_editor.py      🆕 Macro GUI
│   └── assets/
│       ├── icon.ico         🆕 Proper app icon
│       └── icon.png         🆕
├── models/                  (gitignored)
└── logs/                    (gitignored)
```

---

## 🗺️ Implementation Priority

| Priority | Task | Effort | Impact |
|---|---|---|---|
| P0 | Sanitize executor input (security) | 1 hr | 🔴 Critical |
| P0 | Remove DB singleton, fix config pass | 15 min | 🔴 Critical |
| P0 | Fix README hotkey + PyInstaller separator | 10 min | Quick wins |
| P1 | Upgrade Whisper to `small.en` | 5 min | ⬆️⬆️⬆️ Accuracy |
| P1 | Wire up vision context to LLM prompt | 30 min | Unlocks screen-aware reasoning |
| P1 | Add `macro_execution` handler | 30 min | Completes macro system |
| P2 | Floating overlay UI widget | 4-6 hrs | 🖥️ Major UX upgrade |
| P2 | Swap LLM to Qwen 3 / Phi-4 Mini | 2-3 hrs | ⬆️⬆️⬆️ Intent reliability |
| P2 | Swap Vision to Gemma 3 4B | 2-3 hrs | Faster, smaller, better |
| P3 | Add TTS response | 1-2 hrs | Makes Trixie feel alive |
| P3 | Settings panel + macro editor GUI | 6-8 hrs | Complete product feel |
| P3 | Proper app icon + branding | 1 hr | Polish |

---

## Summary

The biggest bang-for-buck improvements:
1. **Security**: Whitelist-based app executor (~1 hr, prevents shell injection)
2. **STT Accuracy**: Just change `"tiny.en"` → `"small.en"` in config (5 seconds of work)
3. **Wire vision context**: Make screen analysis actually useful for follow-up commands
4. **Floating overlay UI**: Transform from invisible tray app to a visible, interactive assistant
5. **Model swap to Qwen 3 + Gemma 3 Vision**: Smaller total footprint (−2.1 GB), better at everything
