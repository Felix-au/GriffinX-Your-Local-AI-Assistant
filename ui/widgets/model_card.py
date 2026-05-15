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
        self.name_lbl.setWordWrap(True)
        top.addWidget(self.name_lbl, 1)

        # Status indicator
        self.status_lbl = QLabel("❓")
        self.status_lbl.setFont(QFont(FONTS["family"], FONTS["size_md"]))
        top.addWidget(self.status_lbl)
        layout.addLayout(top)

        # Progress bar (hidden by default) — tall enough to be visible
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(16)
        self.progress.setFormat("%p%")
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['gauge_track']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                height: 16px;
                text-align: center;
                font-size: 9pt;
                font-weight: bold;
                color: {COLORS['text_primary']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_amber']}, stop:1 {COLORS['accent_gold']});
                border-radius: 5px;
            }}
        """)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Status text line (hidden by default — only shown for errors)
        self.size_lbl = QLabel("")
        self.size_lbl.setFont(QFont(FONTS["family"], FONTS["size_xs"]))
        self.size_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        self.size_lbl.setWordWrap(True)
        self.size_lbl.hide()
        layout.addWidget(self.size_lbl)

    # ── Public API ─────────────────────────────────────────────
    def set_ready(self, path: str = ""):
        self._status = "ready"
        self.status_lbl.setText("✅")
        self.progress.hide()
        self.size_lbl.hide()

    def set_downloading(self, percent: int):
        self._status = "downloading"
        self.status_lbl.setText(f"⏳ {percent}%")
        self.progress.show()
        self.progress.setValue(percent)
        self.size_lbl.hide()

    def set_missing(self):
        self._status = "missing"
        self.status_lbl.setText("❌")
        self.progress.hide()
        self.size_lbl.setText("Not downloaded")
        self.size_lbl.show()

    def set_failed(self, error: str = ""):
        self._status = "failed"
        self.status_lbl.setText("❌")
        self.progress.hide()
        self.size_lbl.setText(f"Failed: {error[:40]}" if error else "Download failed")
        self.size_lbl.setStyleSheet(f"color: {COLORS['error']};")
        self.size_lbl.show()
    # ── Paint ──────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(COLORS["bg_card"]))
        grad.setColorAt(1, QColor(38, 30, 22, 220))
        p.setBrush(grad)
        p.setPen(QPen(QColor(COLORS["border"]), 1))
        p.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2,
                          DIMS["radius_md"], DIMS["radius_md"])
        p.end()

        super().paintEvent(event)
