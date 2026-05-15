"""
Glassmorphism stat card with icon, label, value, and sub-info.
Custom paintEvent with gradient background and subtle drop shadow.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient
from PySide6.QtCore import Qt, QSize

from ui.theme import COLORS, FONTS, DIMS


class StatCard(QWidget):
    """A compact glassmorphism stat card."""

    def __init__(self, icon: str = "", label: str = "", parent=None):
        super().__init__(parent)
        self.setMinimumSize(140, 80)
        self.setMaximumHeight(90)

        self._icon = icon
        self._label = label
        self._value = "—"
        self._sub_info = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        # Top row: icon + label
        top = QHBoxLayout()
        top.setSpacing(6)
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setFont(QFont(FONTS["family"], FONTS["size_md"]))
        self.icon_lbl.setStyleSheet(f"color: {COLORS['accent_amber']};")
        top.addWidget(self.icon_lbl)

        self.label_lbl = QLabel(label)
        self.label_lbl.setFont(QFont(FONTS["family"], FONTS["size_xs"]))
        self.label_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        top.addWidget(self.label_lbl)
        top.addStretch()
        layout.addLayout(top)

        # Value
        self.value_lbl = QLabel("—")
        self.value_lbl.setFont(QFont(FONTS["family"], FONTS["size_lg"], QFont.Weight.Bold))
        self.value_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.value_lbl)

        # Sub-info
        self.sub_lbl = QLabel("")
        self.sub_lbl.setFont(QFont(FONTS["family"], FONTS["size_xs"]))
        self.sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self.sub_lbl)

    def set_value(self, value: str):
        self._value = value
        self.value_lbl.setText(value)

    def set_sub_info(self, text: str):
        self._sub_info = text
        self.sub_lbl.setText(text)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Gradient card background
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(COLORS["bg_card"]))
        grad.setColorAt(1, QColor(28, 28, 50, 220))
        p.setBrush(grad)
        p.setPen(QPen(QColor(COLORS["border"]), 1))
        p.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2,
                          DIMS["radius_md"], DIMS["radius_md"])
        p.end()

        super().paintEvent(event)
