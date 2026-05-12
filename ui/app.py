import sys
import os
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget,
                              QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit)
from PyQt6.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QLinearGradient, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QPropertyAnimation, QEasingCurve, QRect
import logging

class OverlayWidget(QWidget):
    """Floating translucent overlay showing Trixie's live status."""
    
    def __init__(self, start_cb, parent=None):
        super().__init__(parent)
        self.start_cb = start_cb
        self.pulse_phase = 0
        self.status_text = "Idle"
        self.transcript_text = ""
        self.response_text = ""
        self.history_lines = []
        
        self.setWindowTitle("Trixie")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(340, 310)
        
        # Position bottom-right of screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 360, screen.height() - 370)
        
        # Dragging state
        self._drag_pos = None
        
        # Pulse animation timer
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._pulse_tick)
        self.pulse_timer.start(50)
        
        # Feedback buttons
        self.btn_up = QPushButton("👍", self)
        self.btn_up.setGeometry(self.width() - 80, 8, 30, 24)
        self.btn_up.setStyleSheet("background: transparent; color: white; font-size: 14px; border: none;")
        self.btn_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_up.hide()
        
        self.btn_down = QPushButton("👎", self)
        self.btn_down.setGeometry(self.width() - 40, 8, 30, 24)
        self.btn_down.setStyleSheet("background: transparent; color: white; font-size: 14px; border: none;")
        self.btn_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_down.hide()
        
        # Text input box for typing commands
        self.text_input = QLineEdit(self)
        self.text_input.setGeometry(16, self.height() - 36, self.width() - 32, 28)
        self.text_input.setStyleSheet("background: rgba(40, 40, 60, 180); color: white; border: 1px solid rgba(80, 80, 120, 150); border-radius: 14px; padding: 0 12px;")
        self.text_input.setPlaceholderText("Type a command and press Enter...")
        
    def show_feedback_buttons(self):
        self.btn_up.show()
        self.btn_down.show()
        
    def hide_feedback_buttons(self):
        self.btn_up.hide()
        self.btn_down.hide()
        
    def _pulse_tick(self):
        if self.status_text == "Listening...":
            self.pulse_phase = (self.pulse_phase + 3) % 360
            self.update()
    
    def set_status(self, status):
        self.status_text = status
        self.update()
        
    def set_transcript(self, text):
        self.transcript_text = text
        self.update()
        
    def set_response(self, text):
        self.response_text = text
        self.update()
        
    def add_history(self, line):
        self.history_lines.insert(0, line)
        if len(self.history_lines) > 3:
            self.history_lines = self.history_lines[:3]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background: dark glassmorphic rounded rect
        p.setBrush(QColor(18, 18, 24, 220))
        p.setPen(QPen(QColor(80, 80, 120, 100), 1))
        p.drawRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        
        # Header bar gradient
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(90, 60, 200, 180))
        grad.setColorAt(1, QColor(40, 120, 220, 180))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self.width(), 40, 16, 16)
        p.drawRect(0, 20, self.width(), 20)
        
        # Title
        p.setPen(QColor(255, 255, 255))
        title_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        p.setFont(title_font)
        p.drawText(16, 26, "◉ Trixie")
        
        # Status indicator
        status_font = QFont("Segoe UI", 9)
        p.setFont(status_font)
        
        # Status dot color
        if self.status_text == "Listening...":
            import math
            alpha = int(128 + 127 * math.sin(math.radians(self.pulse_phase)))
            dot_color = QColor(0, 220, 100, alpha)
        elif "Executing" in self.status_text or "Thinking" in self.status_text:
            dot_color = QColor(255, 180, 0)
        elif "Error" in self.status_text or "Failed" in self.status_text:
            dot_color = QColor(255, 60, 60)
        else:
            dot_color = QColor(120, 120, 160)
        
        p.setBrush(dot_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(16, 52, 10, 10)
        
        p.setPen(QColor(200, 200, 220))
        p.drawText(32, 62, self.status_text)
        
        # Separator
        p.setPen(QPen(QColor(60, 60, 90), 1))
        p.drawLine(16, 75, self.width() - 16, 75)
        
        y = 95
        
        # Transcript bubble
        if self.transcript_text:
            p.setPen(QColor(140, 160, 255))
            small_font = QFont("Segoe UI", 8)
            p.setFont(small_font)
            p.drawText(16, y, "YOU:")
            y += 16
            p.setPen(QColor(220, 220, 240))
            p.setFont(QFont("Segoe UI", 9))
            
            rect = p.boundingRect(QRect(16, y, self.width() - 32, 200), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.transcript_text)
            p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.transcript_text)
            y += rect.height() + 10
        
        # Response bubble
        if self.response_text:
            p.setPen(QColor(100, 220, 160))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(16, y, "TRIXIE:")
            y += 16
            p.setPen(QColor(200, 240, 210))
            p.setFont(QFont("Segoe UI", 9))
            
            rect = p.boundingRect(QRect(16, y, self.width() - 32, 200), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.response_text)
            p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.response_text)
            y += rect.height() + 10
        
        # History section
        if self.history_lines:
            p.setPen(QPen(QColor(60, 60, 90), 1))
            p.drawLine(16, y, self.width() - 16, y)
            y += 16
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor(100, 100, 130))
            for line in self.history_lines:
                rect = p.boundingRect(QRect(16, y, self.width() - 32, 40), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, line)
                p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, line)
                y += rect.height() + 5
        
        p.end()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class UIEngine(QObject):
    # Signals for cross-thread communication
    status_update = pyqtSignal(str)
    transcript_update = pyqtSignal(str)
    response_update = pyqtSignal(str)
    history_update = pyqtSignal(str)
    feedback_signal = pyqtSignal(str)
    text_command_signal = pyqtSignal(str)
    
    def __init__(self, start_listening_callback, quit_callback, feedback_callback, text_command_callback):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.start_listening_cb = start_listening_callback
        self.quit_cb = quit_callback
        self.feedback_cb = feedback_callback
        self.text_cmd_cb = text_command_callback
        
        # Create a branded icon (purple gradient circle)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, 32, 32)
        grad.setColorAt(0, QColor(90, 60, 200))
        grad.setColorAt(1, QColor(40, 120, 220))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
        painter.end()
        self.icon = QIcon(pixmap)
        
        # System tray
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon)
        self.tray.setVisible(True)
        self.tray.setToolTip("Trixie — Your PC, Your Voice, No Cloud.")
        
        # Tray menu
        self.menu = QMenu()
        self.status_action = self.menu.addAction("Status: Idle")
        self.status_action.setEnabled(False)
        self.menu.addSeparator()
        
        self.show_overlay_action = self.menu.addAction("Show/Hide Overlay")
        self.show_overlay_action.triggered.connect(self._toggle_overlay)
        
        self.record_action = self.menu.addAction("Push to Talk (Ctrl + CapsLock)")
        self.record_action.triggered.connect(self.start_listening_cb)
        self.menu.addSeparator()
        
        self.quit_action = self.menu.addAction("Quit")
        self.quit_action.triggered.connect(self.quit_app)
        self.tray.setContextMenu(self.menu)
        
        # Floating overlay widget
        self.overlay = OverlayWidget(start_cb=self.start_listening_cb)
        self.overlay.show()
        
        # Wire signals
        self.status_update.connect(self._update_status_ui)
        self.transcript_update.connect(self.overlay.set_transcript)
        self.response_update.connect(self.overlay.set_response)
        self.history_update.connect(self.overlay.add_history)
        self.feedback_signal.connect(self.feedback_cb)
        self.text_command_signal.connect(self.text_cmd_cb)
        
        # Connect buttons
        self.overlay.btn_up.clicked.connect(lambda: self.feedback_signal.emit("yes"))
        self.overlay.btn_down.clicked.connect(lambda: self.feedback_signal.emit("no"))
        
        # Connect text input
        self.overlay.text_input.returnPressed.connect(self._handle_text_input)
        
    def _handle_text_input(self):
        text = self.overlay.text_input.text().strip()
        if text:
            self.overlay.text_input.clear()
            self.text_command_signal.emit(text)
        
    def _toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()
        
    def _update_status_ui(self, msg):
        self.status_action.setText(f"Status: {msg}")
        self.overlay.set_status(msg)
        # Only show balloon for important events, not every status change
        if msg not in ["Idle", "Listening..."]:
            self.tray.showMessage("Trixie", msg, QSystemTrayIcon.MessageIcon.Information, 2000)

    def set_status(self, msg):
        self.status_update.emit(msg)
    
    def set_transcript(self, text):
        self.transcript_update.emit(text)
    
    def set_response(self, text):
        self.response_update.emit(text)
    
    def add_history(self, line):
        self.history_update.emit(line)

    def show_feedback_buttons(self):
        self.overlay.show_feedback_buttons()
        
    def hide_feedback_buttons(self):
        self.overlay.hide_feedback_buttons()

    def quit_app(self):
        self.overlay.close()
        self.quit_cb()
        self.app.quit()
        
    def run(self):
        self.logger.info("Starting UI event loop...")
        sys.exit(self.app.exec())
