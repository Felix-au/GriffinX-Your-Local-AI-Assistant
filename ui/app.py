import sys
import os
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget,
                              QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit)
from PySide6.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QLinearGradient, QPen, QImage
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QPropertyAnimation, QEasingCurve, QRect
import logging

def _resolve_asset_path(filename):
    """Resolve an asset path that works in both dev and PyInstaller frozen mode."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", filename)

class OverlayWidget(QWidget):
    """Floating translucent overlay showing Trixie's live status."""
    
    logo_clicked = Signal()  # emitted when user clicks the logo/header area"
    
    def __init__(self, toggle_cb, parent=None):
        super().__init__(parent)
        self.toggle_cb = toggle_cb
        self.pulse_phase = 0
        self.status_text = "Idle"
        self.transcript_text = ""
        self.response_text = ""
        self.history_lines = []
        self.is_ball_mode = True
        self.ball_size = 66  # 10% larger than original 60
        self.ball_x = 40
        self.ball_y = 10
        
        # Load branded assets
        self.ball_pixmap = None
        circular_path = _resolve_asset_path("trixie-circular.jpeg")
        if os.path.exists(circular_path):
            pm = QPixmap(circular_path)
            if not pm.isNull():
                self.ball_pixmap = pm.scaled(self.ball_size, self.ball_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.setWindowTitle("Trixie: Your Local AI Assistant")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set window icon
        ico_path = _resolve_asset_path("trixie.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))
        self.setFixedSize(340, 260)
        self.setMouseTracking(True)
        
        # Load logo for expanded header
        self.logo_pixmap = None
        logo_path = _resolve_asset_path("trixie.jpeg")
        if os.path.exists(logo_path):
            pm = QPixmap(logo_path)
            if not pm.isNull():
                self.logo_pixmap = pm.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        # Position bottom-right of screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 360, screen.height() - 320)
        
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
        self.btn_minimize = QPushButton("×", self)
        self.btn_minimize.setGeometry(self.width() - 36, 8, 24, 24)
        self.btn_minimize.setStyleSheet("""
            QPushButton {
                background: rgba(40, 30, 20, 200);
                color: #F0C060;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
                border: 1px solid #5C4A30;
                padding-bottom: 2px; /* Center the × vertically */
            }
            QPushButton:hover {
                background: rgba(60, 50, 40, 220);
                color: #FFE080;
                border-color: #D4A044;
            }
        """)
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
        
        # Apply default ball mode layout
        if self.is_ball_mode:
            self.text_input.hide()
            self.btn_minimize.hide()
            self._update_ball_layout()
        
    def _update_ball_layout(self):
        if not self.is_ball_mode:
            return
        
        # Suppress painting during geometry changes to prevent black box flicker
        self.setUpdatesEnabled(False)
        
        old_pos = self.pos()
        show_bubble = bool(self.response_text)
        show_input = self.text_input.isVisible()
        bs = self.ball_size
        
        # Wider bubble for better readability
        new_w = 300 if show_bubble else (bs + 80)
        new_h = bs + 20
        self.ball_x = (new_w - bs) // 2
        self.ball_y = 10
        
        self.bubble_h = 0
        if show_bubble:
            from PySide6.QtGui import QFontMetrics
            font = QFont("Segoe UI", 10)
            metrics = QFontMetrics(font)
            rect = metrics.boundingRect(0, 0, new_w - 40, 1000, 
                                       Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, 
                                       self.response_text)
            self.bubble_h = max(40, rect.height() + 25)
            new_h += self.bubble_h + 20
            self.ball_y = self.bubble_h + 30
            
        if show_input:
            new_h += 45
        
        # Atomic geometry change — set size + position in one call to prevent jump
        self.setMinimumSize(new_w, new_h)
        self.setMaximumSize(new_w, new_h)
        self.setGeometry(old_pos.x(), old_pos.y(), new_w, new_h)
        
        self.btn_up.setGeometry(self.ball_x - 35, self.ball_y + 15, 30, 30)
        self.btn_down.setGeometry(self.ball_x + bs + 5, self.ball_y + 15, 30, 30)
        
        if show_input:
            self.text_input.setGeometry(15, self.ball_y + bs + 15, new_w - 30, 28)
        
        self.setUpdatesEnabled(True)

    def toggle_ball_mode(self):
        self.is_ball_mode = not self.is_ball_mode
        self.setUpdatesEnabled(False)
        if self.is_ball_mode:
            self.text_input.hide()
            self.btn_minimize.hide()
            self._update_ball_layout()
        else:
            old_pos = self.pos()
            self.setMinimumSize(340, 260)
            self.setMaximumSize(340, 260)
            self.setGeometry(old_pos.x(), old_pos.y(), 340, 260)
            self.text_input.show()
            self.btn_minimize.show()
            self.btn_up.setGeometry(self.width() - 80, 8, 30, 24)
            self.btn_down.setGeometry(self.width() - 40, 8, 30, 24)
        self.setUpdatesEnabled(True)
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
        elif self.is_ball_mode:
            # Subtle idle breathing glow
            self.pulse_phase = (self.pulse_phase + 5) % 360
            self.update()
    
    def set_status(self, status):
        self.status_text = status
        self.update()
        
    def set_transcript(self, text):
        self.transcript_text = text
        # Clear old response immediately when a new prompt starts
        if text:
            self.response_text = ""
            
        if not self.is_ball_mode:
            self._update_expanded_layout()
        # In ball mode, transcript isn't displayed — just repaint, don't resize
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
        else:
            self._update_expanded_layout()
            
        self.update()
        
    def clear_response(self):
        self.response_text = ""
        if self.is_ball_mode:
            self._update_ball_layout()
        else:
            self._update_expanded_layout()
        self.update()

    def _update_expanded_layout(self):
        """Dynamically resize the expanded window upwards based on content."""
        from PySide6.QtGui import QFontMetrics
        y = 95 # Start of chat area
        
        # Measure Transcript
        if self.transcript_text:
            metrics = QFontMetrics(QFont("Segoe UI", 10))
            rect = metrics.boundingRect(QRect(0, 0, self.width() - 32, 2000), 
                                       Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, 
                                       self.transcript_text)
            y += 14 + rect.height() + 12
            
        # Measure Response
        if self.response_text:
            metrics = QFontMetrics(QFont("Segoe UI", 10))
            rect = metrics.boundingRect(QRect(0, 0, self.width() - 32, 2000), 
                                       Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, 
                                       self.response_text)
            y += 14 + rect.height() + 12
            
        # Add space for the bottom input box (roughly 50px)
        new_h = max(260, y + 50)
        
        old_h = self.height()
        if new_h != old_h:
            old_pos = self.pos()
            delta = new_h - old_h
            # Atomic geometry change — grow/shrink upwards
            self.setMinimumSize(self.width(), new_h)
            self.setMaximumSize(self.width(), new_h)
            self.setGeometry(old_pos.x(), old_pos.y() - delta, self.width(), new_h)
            # Reposition internal buttons
            self.btn_minimize.setGeometry(self.width() - 30, 8, 20, 20)
            self.text_input.setGeometry(16, self.height() - 36, self.width() - 32, 28)



    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.is_ball_mode:
            import math
            bx = self.ball_x
            by = self.ball_y
            bs = self.ball_size
            glow_size = bs + 14
            cx = bx - 7
            cy = by - 7
            
            # Pulse if listening — orbiting particle ring
            if self.status_text == "Listening...":
                p.setBrush(Qt.BrushStyle.NoBrush)
                # Subtle breathing ring
                breath = int(80 + 60 * math.sin(math.radians(self.pulse_phase * 0.7)))
                p.setPen(QPen(QColor(50, 255, 100, breath), 2))
                p.drawEllipse(cx, cy, glow_size, glow_size)
                
                # 6 orbiting particles with trails
                center_x = bx + bs / 2
                center_y = by + bs / 2
                orbit_r = (glow_size) / 2 + 2
                num_particles = 6
                for i in range(num_particles):
                    angle = math.radians(self.pulse_phase * 2 + i * (360 / num_particles))
                    # Lead particle
                    px = center_x + orbit_r * math.cos(angle)
                    py = center_y + orbit_r * math.sin(angle)
                    # Glow
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(50, 255, 100, 40))
                    p.drawEllipse(int(px) - 6, int(py) - 6, 12, 12)
                    # Core dot
                    p.setBrush(QColor(50, 255, 100, 220))
                    p.drawEllipse(int(px) - 3, int(py) - 3, 6, 6)
                    # 4 trailing dots
                    for t in range(1, 5):
                        trail_angle = angle - math.radians(t * 8)
                        tx = center_x + orbit_r * math.cos(trail_angle)
                        ty = center_y + orbit_r * math.sin(trail_angle)
                        trail_alpha = max(20, 180 - t * 40)
                        trail_size = max(2, 5 - t)
                        p.setBrush(QColor(50, 255, 100, trail_alpha))
                        p.drawEllipse(int(tx) - trail_size // 2, int(ty) - trail_size // 2, trail_size, trail_size)
                
            # Spinning conical sweep if thinking/executing
            elif any(s in self.status_text for s in ["Thinking", "Executing"]):
                p.setBrush(Qt.BrushStyle.NoBrush)
                # Dim track ring
                p.setPen(QPen(QColor(0, 212, 255, 30), 3))
                p.drawEllipse(cx, cy, glow_size, glow_size)
                
                # Spinning 120° arc with cyan→gold gradient
                arc_angle = self.pulse_phase
                # Outer glow arc
                p.setPen(QPen(QColor(0, 212, 255, 50), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(cx, cy, glow_size, glow_size, int(arc_angle * 16), 120 * 16)
                # Inner sharp arc
                p.setPen(QPen(QColor(0, 212, 255, 200), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(cx, cy, glow_size, glow_size, int(arc_angle * 16), 120 * 16)
                
                # Leading head dot with glow
                center_x = bx + bs / 2
                center_y = by + bs / 2
                head_r = (glow_size) / 2 + 1
                head_angle = math.radians(arc_angle + 120)
                hx = center_x + head_r * math.cos(head_angle)
                hy = center_y - head_r * math.sin(head_angle)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(240, 192, 96, 60))
                p.drawEllipse(int(hx) - 8, int(hy) - 8, 16, 16)
                p.setBrush(QColor(240, 192, 96, 255))
                p.drawEllipse(int(hx) - 3, int(hy) - 3, 6, 6)
                
            # Green spinner for transcribing
            elif "Transcribing" in self.status_text:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(50, 255, 100, 30), 3))
                p.drawEllipse(cx, cy, glow_size, glow_size)
                # Spinning green arc
                p.setPen(QPen(QColor(50, 255, 100, 50), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(cx, cy, glow_size, glow_size, int(self.pulse_phase * 16), 120 * 16)
                p.setPen(QPen(QColor(50, 255, 100, 200), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(cx, cy, glow_size, glow_size, int(self.pulse_phase * 16), 120 * 16)
            
            else:
                # Idle state: multi-ring warm amber breathing glow
                center_x = bx + bs / 2
                center_y = by + bs / 2
                p.setBrush(Qt.BrushStyle.NoBrush)
                
                # Inner ring — slow breathe
                inner_alpha = int(80 + 100 * math.sin(math.radians(self.pulse_phase)))
                p.setPen(QPen(QColor(212, 160, 68, inner_alpha), 3))
                p.drawEllipse(cx + 2, cy + 2, glow_size - 4, glow_size - 4)
                
                # Outer ring — faster breathe, lower opacity
                outer_alpha = int(40 + 60 * math.sin(math.radians(self.pulse_phase * 2)))
                p.setPen(QPen(QColor(240, 192, 96, outer_alpha), 2))
                p.drawEllipse(cx - 3, cy - 3, glow_size + 6, glow_size + 6)
            
            # Draw the ball — branded circular image or fallback gradient
            if self.ball_pixmap and not self.ball_pixmap.isNull():
                # Clip to circle for clean edges
                from PySide6.QtGui import QPainterPath
                clip_path = QPainterPath()
                clip_path.addEllipse(float(bx), float(by), float(bs), float(bs))
                p.setClipPath(clip_path)
                p.drawPixmap(bx, by, self.ball_pixmap)
                p.setClipping(False)
                # Subtle border ring
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(255, 255, 255, 80), 2))
                p.drawEllipse(bx, by, bs, bs)
            else:
                # Fallback: gradient ball with "T"
                grad = QLinearGradient(bx, by, bx + bs, by + bs)
                grad.setColorAt(0, QColor(90, 60, 200, 220))
                grad.setColorAt(1, QColor(40, 120, 220, 220))
                p.setBrush(grad)
                p.setPen(QPen(QColor(255, 255, 255, 100), 2))
                p.drawEllipse(bx, by, bs, bs)
                p.setPen(QColor(255, 255, 255))
                p.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
                p.drawText(bx, by, bs, bs, Qt.AlignmentFlag.AlignCenter, "T")
            
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
                from PySide6.QtGui import QPolygonF
                from PySide6.QtCore import QPointF
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
        
        # Header bar gradient — warm brownish tone
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(120, 70, 30, 200))
        grad.setColorAt(1, QColor(160, 100, 50, 190))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self.width(), 40, 16, 16)
        p.drawRect(0, 20, self.width(), 20)
        
        # Logo in header
        logo_x = 12
        if self.logo_pixmap and not self.logo_pixmap.isNull():
            p.drawPixmap(logo_x, 6, self.logo_pixmap)
            logo_x += self.logo_pixmap.width() + 6
        
        # Title — full branding
        p.setPen(QColor(255, 255, 255))
        title_font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        p.setFont(title_font)
        p.drawText(logo_x, 26, "Trixie: Your Local AI Assistant")
        
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
        # Update cursor when hovering over clickable areas
        if not self.is_ball_mode and event.pos().y() < 40:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        elif self.is_ball_mode:
            bs = self.ball_size
            if self.ball_x <= event.pos().x() <= self.ball_x + bs and self.ball_y <= event.pos().y() <= self.ball_y + bs:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            self._click_handled = True
    
    def mouseReleaseEvent(self, event):
        if getattr(event, 'button', lambda: None)() == Qt.MouseButton.LeftButton:
            if not getattr(self, '_click_handled', True):
                # Check if click is on the logo/header area (expanded mode, y < 40)
                if not self.is_ball_mode and event.pos().y() < 40:
                    self.logo_clicked.emit()
                elif self.is_ball_mode:
                    bs = self.ball_size
                    if self.ball_x <= event.pos().x() <= self.ball_x + bs and self.ball_y <= event.pos().y() <= self.ball_y + bs:
                        self._click_timer.start(250)
            self._drag_pos = None
            
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_ball_mode:
            bs = self.ball_size
            if self.ball_x <= event.pos().x() <= self.ball_x + bs and self.ball_y <= event.pos().y() <= self.ball_y + bs:
                self._click_timer.stop()
                self.toggle_ball_mode()


class UIEngine(QObject):
    status_update = Signal(str)
    transcript_update = Signal(str)
    response_update = Signal(str)
    feedback_signal = Signal(str)
    text_command_signal = Signal(str)
    dashboard_requested = Signal()  # emitted when user wants to see dashboard
    
    def __init__(self, toggle_listening_callback, quit_callback, feedback_callback, text_command_callback):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.toggle_listening_cb = toggle_listening_callback
        self.quit_cb = quit_callback
        self.feedback_cb = feedback_callback
        self.text_cmd_cb = text_command_callback
        
        # Load branded icon from assets
        ico_path = _resolve_asset_path("trixie.ico")
        circular_path = _resolve_asset_path("trixie-circular.jpeg")
        
        if os.path.exists(ico_path):
            self.icon = QIcon(ico_path)
            self.app.setWindowIcon(self.icon)
        elif os.path.exists(circular_path):
            self.icon = QIcon(circular_path)
        else:
            # Fallback: programmatic gradient icon
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
        self.tray.setToolTip("Trixie: Your Local AI Assistant")
        
        # Tray menu
        self.menu = QMenu()
        self.status_action = self.menu.addAction("Status: Idle")
        self.status_action.setEnabled(False)
        self.menu.addSeparator()
        
        self.show_overlay_action = self.menu.addAction("Show/Hide Overlay")
        self.show_overlay_action.triggered.connect(self._toggle_overlay)
        
        self.show_dashboard_action = self.menu.addAction("Open Dashboard")
        self.show_dashboard_action.triggered.connect(lambda: self.dashboard_requested.emit())
        
        self.record_action = self.menu.addAction("Push to Talk (Ctrl + CapsLock)")
        self.record_action.triggered.connect(self.toggle_listening_cb)
        self.menu.addSeparator()
        
        self.quit_action = self.menu.addAction("Quit")
        self.quit_action.triggered.connect(self.quit_app)
        self.tray.setContextMenu(self.menu)
        
        # Double-click tray icon → show dashboard
        self.tray.activated.connect(self._tray_activated)
        
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
    
    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.dashboard_requested.emit()
        
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
