"""
Trixie Dashboard — Main QMainWindow with gauges, model cards, activity log, and settings.
"""
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QCheckBox, QTextEdit, QStatusBar, QGridLayout, QFrame
)
from PySide6.QtGui import QFont, QIcon, QColor, QPixmap
from PySide6.QtCore import Qt, Signal

from ui.theme import COLORS, FONTS, DIMS, get_global_stylesheet
from ui.widgets.gauge_widget import GaugeWidget
from ui.widgets.model_card import ModelCard

logger = logging.getLogger(__name__)

# Max activity log entries
_MAX_LOG = 100


class DashboardWindow(QMainWindow):
    """Trixie command center — status, gauges, settings, and activity."""

    setting_changed = Signal(str, object)  # (key, value)

    def __init__(self, version: str = "1.0.0", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Trixie: Your Local AI Assistant  —  v{version}")
        self.setMinimumSize(820, 520)
        self.resize(900, 580)

        self._version = version
        self._log_count = 0

        self._build_ui()

    # ── UI Construction ────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # ── Left column (gauges + model cards) ─────────────────
        left = QVBoxLayout()
        left.setSpacing(14)

        # Header
        header = QHBoxLayout()
        self.status_dot = QLabel("🟢")
        self.status_dot.setFont(QFont(FONTS["family"], FONTS["size_md"]))
        header.addWidget(self.status_dot)

        title = QLabel(f"Trixie: Your Local AI Assistant")
        title.setFont(QFont(FONTS["family"], FONTS["size_xl"], QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent_gold']};")
        header.addWidget(title)
        header.addStretch()

        ver_lbl = QLabel(f"v{self._version}")
        ver_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        header.addWidget(ver_lbl)
        left.addLayout(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        left.addWidget(sep)

        # Gauge row
        gauge_box = QGroupBox("System Resources")
        gauge_layout = QHBoxLayout(gauge_box)
        gauge_layout.setSpacing(10)

        self.gauge_cpu = GaugeWidget("CPU")
        self.gauge_ram = GaugeWidget("RAM")
        self.gauge_gpu = GaugeWidget("GPU")
        self.gauge_vram = GaugeWidget("VRAM")

        for g in (self.gauge_cpu, self.gauge_ram, self.gauge_gpu, self.gauge_vram):
            gauge_layout.addWidget(g)

        # Initialize GPU gauges to N/A
        self.gauge_gpu.set_value(-1)
        self.gauge_vram.set_value(-1)

        left.addWidget(gauge_box)

        # Model cards row
        model_box = QGroupBox("AI Models")
        model_layout = QHBoxLayout(model_box)
        model_layout.setSpacing(10)

        self.card_stt = ModelCard("🎙️", "STT — Whisper", "~1.5 GB")
        self.card_llm = ModelCard("🧠", "LLM — Qwen 3 4B", "~2.5 GB")
        self.card_tts = ModelCard("🔊", "TTS — Piper", "~15 MB")

        for c in (self.card_stt, self.card_llm, self.card_tts):
            model_layout.addWidget(c)

        left.addWidget(model_box)
        left.addStretch()
        root.addLayout(left, 3)

        # ── Right column (activity log + settings) ─────────────
        right = QVBoxLayout()
        right.setSpacing(14)

        # Activity log
        log_box = QGroupBox("📋 Recent Activity")
        log_layout = QVBoxLayout(log_box)
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setPlaceholderText("Activity will appear here...")
        log_layout.addWidget(self.activity_log)
        right.addWidget(log_box, 3)

        # Settings
        settings_box = QGroupBox("⚙️ Settings")
        settings_layout = QVBoxLayout(settings_box)
        settings_layout.setSpacing(10)

        self.chk_startup = QCheckBox("Start at system startup")
        self.chk_startup.setChecked(True)
        self.chk_startup.toggled.connect(lambda v: self.setting_changed.emit("start_at_startup", v))
        settings_layout.addWidget(self.chk_startup)

        self.chk_minimize = QCheckBox("Minimize to tray on close")
        self.chk_minimize.setChecked(True)
        self.chk_minimize.toggled.connect(lambda v: self.setting_changed.emit("minimize_to_tray", v))
        settings_layout.addWidget(self.chk_minimize)

        right.addWidget(settings_box, 1)
        root.addLayout(right, 2)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Trixie is idle  •  Push-to-talk: Ctrl + CapsLock")

    # ── Public API ─────────────────────────────────────────────
    def update_stats(self, stats):
        """Receive SystemStats and update gauges."""
        self.gauge_cpu.set_value(stats.cpu_percent)
        self.gauge_ram.set_value(stats.ram_percent)
        self.gauge_gpu.set_value(stats.gpu_util_percent)

        if stats.gpu_mem_total_mb > 0:
            self.gauge_vram.set_value(stats.gpu_mem_percent)
            self.gauge_vram.set_label(f"VRAM {stats.gpu_mem_used_mb / 1024:.1f}G")
        else:
            self.gauge_vram.set_value(-1)

    def add_activity(self, message: str):
        """Append a timestamped entry to the activity log."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"[{ts}] {message}")
        self._log_count += 1
        if self._log_count > _MAX_LOG:
            # Trim oldest lines
            cursor = self.activity_log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            self._log_count -= 1

    def update_status_bar(self, message: str):
        self.status_bar.showMessage(message)

    def set_status_dot(self, status: str):
        """Update the header status dot based on app state."""
        if "Listen" in status:
            self.status_dot.setText("🟢")
        elif "Think" in status or "Execut" in status:
            self.status_dot.setText("🟡")
        elif "Error" in status or "Failed" in status:
            self.status_dot.setText("🔴")
        else:
            self.status_dot.setText("⚪")

    def apply_settings(self, settings: dict):
        """Apply saved settings to checkboxes without triggering signals."""
        self.chk_startup.blockSignals(True)
        self.chk_startup.setChecked(settings.get("start_at_startup", True))
        self.chk_startup.blockSignals(False)

        self.chk_minimize.blockSignals(True)
        self.chk_minimize.setChecked(settings.get("minimize_to_tray", True))
        self.chk_minimize.blockSignals(False)
