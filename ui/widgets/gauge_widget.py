"""
Animated circular gauge widget (0-100%) using QPainter + QPropertyAnimation.
270° arc with warm amber gradient, smooth OutCubic easing.
Shows 'N/A' when value is -1 (unavailable GPU metrics).
"""
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QConicalGradient
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve, QSize

from ui.theme import COLORS, FONTS


class GaugeWidget(QWidget):
    """Circular gauge that animates from 0-100%. Pass -1 for N/A state."""

    def __init__(self, label: str = "", parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._display_value = 0.0
        self._label = label
        self.setMinimumSize(100, 120)
        self.setMaximumSize(140, 150)

        self._anim = QPropertyAnimation(self, b"displayValue")
        self._anim.setDuration(600)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Animated property ──────────────────────────────────────
    def _get_display_value(self):
        return self._display_value

    def _set_display_value(self, v):
        self._display_value = v
        self.update()

    displayValue = Property(float, _get_display_value, _set_display_value)

    # ── Public API ─────────────────────────────────────────────
    def set_value(self, v: float):
        """Set gauge value. Use -1 for N/A."""
        old = self._value
        self._value = v
        if v < 0:
            self._display_value = -1
            self.update()
            return
        self._anim.stop()
        self._anim.setStartValue(old if old >= 0 else 0)
        self._anim.setEndValue(v)
        self._anim.start()

    def set_label(self, text: str):
        self._label = text
        self.update()

    # ── Paint ──────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height() - 24  # reserve space for label
        size = min(w, h) - 16
        x = (w - size) // 2
        y = 8

        arc_span = 270  # degrees
        start_angle = 135  # start from bottom-left

        # Track
        track_pen = QPen(QColor(COLORS["gauge_track"]), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(track_pen)
        p.drawArc(x, y, size, size, start_angle * 16, arc_span * 16)

        if self._display_value < 0:
            # N/A state
            p.setPen(QColor(COLORS["text_muted"]))
            p.setFont(QFont(FONTS["family"], FONTS["size_lg"], QFont.Weight.Bold))
            p.drawText(x, y, size, size, Qt.AlignmentFlag.AlignCenter, "N/A")
        else:
            # Value arc
            frac = max(0, min(self._display_value / 100.0, 1.0))
            value_span = arc_span * frac

            # Color based on value
            if self._display_value < 50:
                arc_color = QColor(COLORS["accent_green"])
            elif self._display_value < 80:
                arc_color = QColor(COLORS["accent_amber"])
            else:
                arc_color = QColor(COLORS["accent_red"])

            value_pen = QPen(arc_color, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(value_pen)
            p.drawArc(x, y, size, size, start_angle * 16, int(value_span * 16))

            # Percentage text
            p.setPen(QColor(COLORS["text_primary"]))
            p.setFont(QFont(FONTS["family"], FONTS["size_lg"], QFont.Weight.Bold))
            p.drawText(x, y, size, size, Qt.AlignmentFlag.AlignCenter, f"{int(self._display_value)}%")

        # Label below
        p.setPen(QColor(COLORS["text_secondary"]))
        p.setFont(QFont(FONTS["family"], FONTS["size_xs"]))
        p.drawText(0, self.height() - 20, w, 20, Qt.AlignmentFlag.AlignCenter, self._label)

        p.end()
