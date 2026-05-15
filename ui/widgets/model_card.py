"""
Model status card with progress bar for download tracking.
Shows model name, status icon, file size, and animated progress bar.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient
from PySide6.QtCore import Qt

from ui.theme import COLORS, FONTS, DIMS


class ModelCard(QWidget):
    """Widget showing a model's download/ready status with progress bar."""

    def __init__(self, icon: str = "🧠", model_name: str = "", size_label: str = "", parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 90)
        self.setMaximumHeight(100)

        self._status = "unknown"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # Top row: icon + name
        top = QHBoxLayout()
        top.setSpacing(8)
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setFont(QFont(FONTS["family"], FONTS["size_md"]))
        top.addWidget(self.icon_lbl)

        self.name_lbl = QLabel(model_name)
        self.name_lbl.setFont(QFont(FONTS["family"], FONTS["size_sm"], QFont.Weight.Bold))
        self.name_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        top.addWidget(self.name_lbl)
        top.addStretch()

        # Status indicator
        self.status_lbl = QLabel("❓")
        self.status_lbl.setFont(QFont(FONTS["family"], FONTS["size_md"]))
        top.addWidget(self.status_lbl)
        layout.addLayout(top)

        # Progress bar (hidden by default)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(8)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Bottom row: size label
        self.size_lbl = QLabel(size_label)
        self.size_lbl.setFont(QFont(FONTS["family"], FONTS["size_xs"]))
        self.size_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self.size_lbl)

    # ── Public API ─────────────────────────────────────────────
    def set_ready(self, path: str = ""):
        self._status = "ready"
        self.status_lbl.setText("✅")
        self.progress.hide()
        if path:
            self.size_lbl.setText(f"✅ {path}")

    def set_downloading(self, percent: int):
        self._status = "downloading"
        self.status_lbl.setText(f"⏳ {percent}%")
        self.progress.show()
        self.progress.setValue(percent)

    def set_missing(self):
        self._status = "missing"
        self.status_lbl.setText("❌")
        self.progress.hide()
        self.size_lbl.setText("Not downloaded")

    def set_failed(self, error: str = ""):
        self._status = "failed"
        self.status_lbl.setText("❌")
        self.progress.hide()
        self.size_lbl.setText(f"Failed: {error[:40]}" if error else "Download failed")
        self.size_lbl.setStyleSheet(f"color: {COLORS['error']};")

    # ── Paint ──────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(COLORS["bg_card"]))
        grad.setColorAt(1, QColor(28, 28, 50, 220))
        p.setBrush(grad)
        p.setPen(QPen(QColor(COLORS["border"]), 1))
        p.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2,
                          DIMS["radius_md"], DIMS["radius_md"])
        p.end()

        super().paintEvent(event)
