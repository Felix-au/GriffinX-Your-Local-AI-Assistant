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
    
    def __init__(self, toggle_cb, parent=None):
        super().__init__(parent)
        self.toggle_cb = toggle_cb
        self.pulse_phase = 0
        self.status_text = "Idle"
        self.transcript_text = ""
        self.response_text = ""
        self.history_lines = []
        self.is_ball_mode = False
        self.ball_x = 40
        self.ball_y = 10
        
        self.setWindowTitle("Trixie")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(340, 160)
        
        # Position bottom-right of screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 360, screen.height() - 220)
        
        # Dragging state
        self._drag_pos = None
        
        # Click disambiguation timer
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self.toggle_cb)
        
        # Pulse animation timer
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._pulse_tick)
        self.pulse_timer.start(50)
        
        # Response bubble auto-hide timer
        self.response_timer = QTimer(self)
        self.response_timer.setSingleShot(True)
        self.response_timer.timeout.connect(self.clear_response)
        
        # Minimize button
        self.btn_minimize = QPushButton("-", self)
        self.btn_minimize.setGeometry(self.width() - 30, 8, 20, 20)
        self.btn_minimize.setStyleSheet("background: transparent; color: white; font-size: 16px; font-weight: bold; border: none;")
        self.btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_minimize.clicked.connect(self.toggle_ball_mode)
        
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
        
    def _update_ball_layout(self):
        if not self.is_ball_mode:
            return
            
        show_bubble = bool(self.response_text)
        show_input = self.text_input.isVisible()
        
        # Wider bubble for better readability
        new_w = 300 if show_bubble else 140
        new_h = 80
        self.ball_x = (new_w - 60) // 2
        self.ball_y = 10
        
        self.bubble_h = 0
        if show_bubble:
            from PyQt6.QtGui import QFontMetrics
            font = QFont("Segoe UI", 10)
            metrics = QFontMetrics(font)
            # Available width is new_w - 40 (20px padding on each side)
            rect = metrics.boundingRect(0, 0, new_w - 40, 1000, 
                                       Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, 
                                       self.response_text)
            self.bubble_h = max(40, rect.height() + 25)
            new_h += self.bubble_h + 20 # Tail and spacing
            self.ball_y = self.bubble_h + 30
            
        if show_input:
            new_h += 45
            
        self.setFixedSize(new_w, new_h)
        self.btn_up.setGeometry(self.ball_x - 35, self.ball_y + 15, 30, 30)
        self.btn_down.setGeometry(self.ball_x + 65, self.ball_y + 15, 30, 30)
        
        if show_input:
            self.text_input.setGeometry(15, self.ball_y + 75, new_w - 30, 28)

    def toggle_ball_mode(self):
        self.is_ball_mode = not self.is_ball_mode
        if self.is_ball_mode:
            self.text_input.hide()
            self.btn_minimize.hide()
            self._update_ball_layout()
        else:
            self.setFixedSize(340, 160)
            self.text_input.show()
            self.btn_minimize.show()
            self.btn_up.setGeometry(self.width() - 80, 8, 30, 24)
            self.btn_down.setGeometry(self.width() - 40, 8, 30, 24)
        self.update()
        
    def toggle_ball_text_input(self):
        if not self.is_ball_mode:
            return
        if self.text_input.isVisible():
            self.text_input.hide()
        else:
            self.text_input.show()
            self.text_input.setFocus()
        self._update_ball_layout()
        self.update()
        
    def show_feedback_buttons(self):
        self.btn_up.show()
        self.btn_down.show()
        
    def hide_feedback_buttons(self):
        self.btn_up.hide()
        self.btn_down.hide()
        
    def _pulse_tick(self):
        if self.status_text == "Listening...":
            self.pulse_phase = (self.pulse_phase + 6) % 360
            self.update()
        elif any(s in self.status_text for s in ["Thinking", "Executing", "Transcribing"]):
            self.pulse_phase = (self.pulse_phase + 16) % 360
            self.update()
    
    def set_status(self, status):
        self.status_text = status
        self.update()
        
    def set_transcript(self, text):
        self.transcript_text = text
        self.update()
        
    def set_response(self, text):
        self.response_text = text
        if self.is_ball_mode:
            self._update_ball_layout()
            
            # Dynamic duration: 500ms per word, bounded by [5s, 15s]
            word_count = len(text.split())
            duration_ms = max(5000, min(15000, word_count * 500))
            
            # Restart timer (stops previous if running)
            self.response_timer.start(duration_ms)
            
        self.update()
        
    def clear_response(self):
        self.response_text = ""
        if self.is_ball_mode:
            self._update_ball_layout()
        self.update()


    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.is_ball_mode:
            # Draw the ball overlay
            grad = QLinearGradient(self.ball_x, self.ball_y, self.ball_x + 60, self.ball_y + 60)
            grad.setColorAt(0, QColor(90, 60, 200, 220))
            grad.setColorAt(1, QColor(40, 120, 220, 220))
            
            bx = self.ball_x
            by = self.ball_y
            cx = bx - 5
            cy = by - 5
            
            # Pulse if listening
            if self.status_text == "Listening...":
                import math
                alpha = int(128 + 127 * math.sin(math.radians(self.pulse_phase)))
                p.setBrush(Qt.BrushStyle.NoBrush)
                # Outer soft neon glow
                p.setPen(QPen(QColor(50, 255, 100, alpha // 3), 8))
                p.drawEllipse(cx, cy, 70, 70)
                # Inner sharp neon ring
                p.setPen(QPen(QColor(50, 255, 100, alpha), 2))
                p.drawEllipse(cx, cy, 70, 70)
                
            # Neon arc spinner if thinking/executing/transcribing
            elif any(s in self.status_text for s in ["Thinking", "Executing", "Transcribing"]):
                p.setBrush(Qt.BrushStyle.NoBrush)
                # Green for transcribing, Cyan for thinking/executing
                color = QColor(50, 255, 100) if "Transcribing" in self.status_text else QColor(0, 255, 255)
                
                # Outer soft neon glow arc
                p.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 60), 8))
                p.drawArc(cx, cy, 70, 70, self.pulse_phase * 16, 140 * 16)
                # Inner sharp neon arc
                p.setPen(QPen(color, 3))
                p.drawArc(cx, cy, 70, 70, self.pulse_phase * 16, 140 * 16)
                
            p.setBrush(grad)
            p.setPen(QPen(QColor(255, 255, 255, 100), 2))
            p.drawEllipse(bx, by, 60, 60)
            
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            p.drawText(bx, by, 60, 60, Qt.AlignmentFlag.AlignCenter, "T")
            
            # Draw speech bubble if there is a response
            if self.response_text:
                # More translucent background
                p.setBrush(QColor(15, 15, 25, 160))
                p.setPen(QPen(QColor(100, 220, 160, 150), 1.5))
                
                # Bubble rect: based on dynamic height
                bubble_rect = QRect(10, 10, self.width() - 20, self.bubble_h)
                p.drawRoundedRect(bubble_rect, 12, 12)
                
                # Draw small tail pointing to the ball
                tail_base_y = bubble_rect.bottom()
                tail = [
                    (self.width() // 2 - 12, tail_base_y),
                    (self.width() // 2 + 12, tail_base_y),
                    (self.width() // 2, tail_base_y + 12)
                ]
                p.setBrush(QColor(15, 15, 25, 160))
                p.setPen(Qt.PenStyle.NoPen)
                from PyQt6.QtGui import QPolygonF
                from PyQt6.QtCore import QPointF
                poly = QPolygonF([QPointF(x, y) for x, y in tail])
                p.drawPolygon(poly)
                
                # Redraw tail border
                p.setPen(QPen(QColor(100, 220, 160, 150), 1.5))
                p.drawLine(tail[0][0], tail[0][1], tail[2][0], tail[2][1])
                p.drawLine(tail[1][0], tail[1][1], tail[2][0], tail[2][1])
                
                # Text inside bubble
                p.setPen(QColor(230, 250, 240))
                p.setFont(QFont("Segoe UI", 10))
                text_rect = bubble_rect.adjusted(12, 10, -12, -10)
                p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.response_text)
                
            p.end()
            return
            
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
            small_font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            p.setFont(small_font)
            p.drawText(16, y, "YOU:")
            y += 3 # Move below the "YOU:" label
            
            p.setPen(QColor(220, 220, 240))
            p.setFont(QFont("Segoe UI", 10))
            rect = p.boundingRect(QRect(16, y, self.width() - 32, 200), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.transcript_text)
            p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.transcript_text)
            y += rect.height() + 20 # Large separation before next speaker
        
        # Response bubble
        if self.response_text:
            p.setPen(QColor(100, 220, 160))
            small_font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            p.setFont(small_font)
            p.drawText(16, y, "TRIXIE:")
            y += 3 # Move below the "TRIXIE:" label
            
            p.setPen(QColor(200, 240, 210))
            p.setFont(QFont("Segoe UI", 10))
            rect = p.boundingRect(QRect(16, y, self.width() - 32, 200), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.response_text)
            p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.response_text)
            y += rect.height() + 10
        
        p.end()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._click_handled = False
        elif event.button() == Qt.MouseButton.RightButton and self.is_ball_mode:
            self.toggle_ball_text_input()
    
    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            self._click_handled = True
    
    def mouseReleaseEvent(self, event):
        if getattr(event, 'button', lambda: None)() == Qt.MouseButton.LeftButton:
            if not getattr(self, '_click_handled', True) and self.is_ball_mode:
                if self.ball_x <= event.pos().x() <= self.ball_x + 60 and self.ball_y <= event.pos().y() <= self.ball_y + 60:
                    self._click_timer.start(250)
            self._drag_pos = None
            
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_ball_mode:
            if self.ball_x <= event.pos().x() <= self.ball_x + 60 and self.ball_y <= event.pos().y() <= self.ball_y + 60:
                self._click_timer.stop()
                self.toggle_ball_mode()


class UIEngine(QObject):
    # Signals for cross-thread communication
    status_update = pyqtSignal(str)
    transcript_update = pyqtSignal(str)
    response_update = pyqtSignal(str)
    feedback_signal = pyqtSignal(str)
    text_command_signal = pyqtSignal(str)
    
    def __init__(self, toggle_listening_callback, quit_callback, feedback_callback, text_command_callback):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.toggle_listening_cb = toggle_listening_callback
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
        self.record_action.triggered.connect(self.toggle_listening_cb)
        self.menu.addSeparator()
        
        self.quit_action = self.menu.addAction("Quit")
        self.quit_action.triggered.connect(self.quit_app)
        self.tray.setContextMenu(self.menu)
        
        # Floating overlay widget
        self.overlay = OverlayWidget(toggle_cb=self.toggle_listening_cb)
        self.overlay.show()
        
        # Wire signals
        self.status_update.connect(self._update_status_ui)
        self.transcript_update.connect(self.overlay.set_transcript)
        self.response_update.connect(self.overlay.set_response)
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
            if self.overlay.is_ball_mode:
                self.overlay.toggle_ball_text_input()
        
    def _toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()
        
    def _update_status_ui(self, msg):
        self.status_action.setText(f"Status: {msg}")
        self.overlay.set_status(msg)

    def set_status(self, msg):
        self.status_update.emit(msg)
    
    def set_transcript(self, text):
        self.transcript_update.emit(text)
    
    def set_response(self, text):
        self.response_update.emit(text)
    


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
