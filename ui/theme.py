"""
Trixie Design System — Dark-mode-first with warm amber/gold accent palette.
Provides colors, fonts, dimensions, a global QSS stylesheet, and helpers.
"""

# ── Color Palette ───────────────────────────────────────────────
COLORS = {
    "bg_primary":     "#11100B",     # Deep warm black with gold undertone
    "bg_secondary":   "#1A1610",     # Dark golden-brown
    "bg_card":        "#231D14",     # Card surfaces — warm golden-brown
    "bg_card_hover":  "#302618",     # Card hover — lighter gold-brown
    "bg_input":       "#15120D",     # Input fields
    "border":         "#3D3222",     # Borders — golden-brown
    "border_accent":  "#5C4A30",     # Active borders — rich gold
    "text_primary":   "#F2EADB",     # Warm creamy white
    "text_secondary": "#B0A080",     # Labels — warm gold-gray
    "text_muted":     "#7A6B50",     # Dimmed — golden muted
    "accent_amber":   "#D4A044",     # Primary accent — warm amber
    "accent_gold":    "#F0C060",     # Secondary accent — bright gold
    "accent_green":   "#10B981",     # Ready / success
    "accent_red":     "#EF4444",     # Error
    "accent_orange":  "#F59E0B",     # Warning / loading
    "accent_cyan":    "#00D4FF",     # Thinking state (neon)
    "gauge_track":    "#261E14",     # Gauge background — golden-brown
    "success":        "#10B981",
    "warning":        "#F59E0B",
    "error":          "#EF4444",
    "gold_glow":      "rgba(240, 192, 96, 50)",  # Subtle gold glow for premium elements
}

# ── Typography ──────────────────────────────────────────────────
FONTS = {
    "family":    "Segoe UI",
    "mono":      "Consolas",
    "size_xs":   9,
    "size_sm":   10,
    "size_md":   12,
    "size_lg":   14,
    "size_xl":   18,
    "size_xxl":  24,
}

# ── Dimensions ──────────────────────────────────────────────────
DIMS = {
    "radius_sm":  6,
    "radius_md":  10,
    "radius_lg":  16,
    "spacing_xs": 4,
    "spacing_sm": 8,
    "spacing_md": 16,
    "spacing_lg": 24,
    "spacing_xl": 32,
}


def get_global_stylesheet() -> str:
    """Full QSS stylesheet for the dashboard and all widgets."""
    c = COLORS
    f = FONTS
    d = DIMS
    return f"""
    /* ── Main Window ─────────────────────────────── */
    QMainWindow {{
        background-color: {c['bg_primary']};
        color: {c['text_primary']};
    }}

    /* ── Labels ──────────────────────────────────── */
    QLabel {{
        color: {c['text_primary']};
        font-family: "{f['family']}";
        font-size: {f['size_sm']}pt;
        background: transparent;
    }}
    QLabel[class="heading"] {{
        font-size: {f['size_lg']}pt;
        font-weight: bold;
        color: {c['accent_gold']};
    }}
    QLabel[class="subtext"] {{
        font-size: {f['size_xs']}pt;
        color: {c['text_secondary']};
    }}

    /* ── Buttons ─────────────────────────────────── */
    QPushButton {{
        background-color: {c['bg_card']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: {d['radius_sm']}px;
        padding: 6px 14px;
        font-family: "{f['family']}";
        font-size: {f['size_sm']}pt;
    }}
    QPushButton:hover {{
        background-color: {c['bg_card_hover']};
        border: 1px solid {c['accent_gold']};
    }}
    QPushButton:pressed {{
        background-color: {c['accent_amber']};
        color: {c['bg_primary']};
    }}

    /* ── Checkboxes ──────────────────────────────── */
    QCheckBox {{
        color: {c['text_primary']};
        font-family: "{f['family']}";
        font-size: {f['size_sm']}pt;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {c['border_accent']};
        background: {c['bg_input']};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c['accent_gold']};
    }}
    QCheckBox::indicator:checked {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {c['accent_amber']}, stop:1 {c['accent_gold']});
        border-color: {c['accent_gold']};
    }}

    /* ── Progress Bar ────────────────────────────── */
    QProgressBar {{
        background-color: {c['gauge_track']};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
        font-size: 0px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['accent_amber']}, stop:1 {c['accent_gold']});
        border-radius: 4px;
    }}

    /* ── Scroll Area ─────────────────────────────── */
    QScrollArea {{
        background: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: {c['bg_secondary']};
        width: 8px;
        border-radius: 4px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border_accent']};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['accent_amber']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* ── Text Edit / List (Activity Log) ─────────── */
    QTextEdit, QPlainTextEdit {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: {d['radius_sm']}px;
        font-family: "{f['mono']}";
        font-size: {f['size_xs']}pt;
        padding: 6px;
        selection-background-color: {c['accent_amber']};
    }}

    /* ── Group Box ────────────────────────────────── */
    QGroupBox {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border']};
        border-radius: {d['radius_md']}px;
        margin-top: 12px;
        padding: 16px 10px 10px 10px;
        font-family: "{f['family']}";
        font-size: {f['size_sm']}pt;
        color: {c['text_secondary']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 6px;
        color: {c['accent_gold']};
    }}

    /* ── Status Bar ───────────────────────────────── */
    QStatusBar {{
        background: {c['bg_secondary']};
        color: {c['text_muted']};
        font-size: {f['size_xs']}pt;
        border-top: 1px solid {c['border']};
    }}
    """


def card_style(hover: bool = True) -> str:
    """Inline stylesheet for a glassmorphism card widget."""
    c = COLORS
    d = DIMS
    base = (
        f"background-color: {c['bg_card']};"
        f"border: 1px solid {c['border']};"
        f"border-radius: {d['radius_md']}px;"
        f"padding: {d['spacing_md']}px;"
    )
    if hover:
        base += (
            f" QWidget:hover {{ background-color: {c['bg_card_hover']};"
            f" border-color: {c['border_accent']}; }}"
        )
    return base
