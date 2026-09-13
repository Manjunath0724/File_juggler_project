"""Theme definitions, color tokens, and modern QSS stylesheet generator for File Juggler."""
from typing import Dict
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect

DARK_PALETTE = {
    "bg_main": "#090d16",          # Deep Obsidian Space Canvas
    "bg_surface": "#111827",       # Slate 900 Card Surface
    "bg_surface_alt": "#1a2234",   # Slate 800 Sub-surface
    "bg_hover": "#243048",         # Slate 700 Hover
    "border": "#1f293d",           # Card Border
    "border_hover": "#334155",     # Card Border Hover
    "border_input": "#2d3748",     # Input & Button Border
    "border_focus": "#3b82f6",     # Electric Blue Focus
    "text_primary": "#f8fafc",     # Slate 50
    "text_secondary": "#94a3b8",   # Slate 400
    "text_muted": "#64748b",       # Slate 500
    "accent": "#3b82f6",           # Blue 500
    "accent_hover": "#2563eb",     # Blue 600
    "accent_subtle": "rgba(59, 130, 246, 0.12)",
    "success": "#10b981",          # Emerald 500
    "success_bg": "rgba(16, 185, 129, 0.14)",
    "warning": "#f59e0b",          # Amber 500
    "warning_bg": "rgba(245, 158, 11, 0.14)",
    "danger": "#ef4444",           # Rose 500
    "danger_bg": "rgba(239, 68, 68, 0.14)",
    "table_alt_row": "#0d1320",
    "badge_bg": "#1e293b",
    "badge_text": "#94a3b8",
    "badge_border": "#334155",
    "input_bg": "#131c2e",
    "btn_bg": "#1a2234",
    "btn_hover": "#243048",
    "btn_pressed": "#111827",
    "radio_border": "#475569",
    "shadow_color": QColor(0, 0, 0, 95),
}

LIGHT_PALETTE = {
    "bg_main": "#f1f5f9",          # Slate 100 Canvas (clear visual distinction from white cards)
    "bg_surface": "#ffffff",       # Pure White Card Surface
    "bg_surface_alt": "#f8fafc",   # Slate 50 Sub-surface
    "bg_hover": "#e2e8f0",         # Slate 200 Hover
    "border": "#e2e8f0",           # Delicate Slate Card Border
    "border_hover": "#93c5fd",     # Soft Sky Blue on Card Hover
    "border_input": "#cbd5e1",     # Slate 300 Sharp Input Border
    "border_focus": "#2563eb",     # Royal Blue Focus
    "text_primary": "#0f172a",     # Slate 900 Deep Contrast Text
    "text_secondary": "#475569",   # Slate 600 Clear Readable Secondary Text
    "text_muted": "#64748b",       # Slate 500
    "accent": "#2563eb",           # Royal Blue 600
    "accent_hover": "#1d4ed8",     # Blue 700
    "accent_subtle": "rgba(37, 99, 235, 0.08)",
    "success": "#059669",          # Emerald 600
    "success_bg": "rgba(5, 150, 105, 0.10)",
    "warning": "#d97706",          # Amber 600
    "warning_bg": "rgba(217, 119, 6, 0.10)",
    "danger": "#dc2626",           # Rose 600
    "danger_bg": "rgba(220, 38, 38, 0.10)",
    "table_alt_row": "#f8fafc",
    "badge_bg": "#e2e8f0",
    "badge_text": "#334155",
    "badge_border": "#cbd5e1",
    "input_bg": "#ffffff",
    "btn_bg": "#ffffff",
    "btn_hover": "#f1f5f9",
    "btn_pressed": "#e2e8f0",
    "radio_border": "#94a3b8",
    "shadow_color": QColor(15, 23, 42, 16),
}


def get_theme_palette(theme: str = "dark") -> QPalette:
    """Create a Qt Application Palette explicitly synchronized to the theme."""
    pal = QPalette()
    p = DARK_PALETTE if theme == "dark" else LIGHT_PALETTE

    bg_main = QColor(p["bg_main"])
    bg_surface = QColor(p["bg_surface"])
    text_primary = QColor(p["text_primary"])
    accent = QColor(p["accent"])
    btn_bg = QColor(p["btn_bg"])

    pal.setColor(QPalette.Window, bg_main)
    pal.setColor(QPalette.WindowText, text_primary)
    pal.setColor(QPalette.Base, bg_surface)
    pal.setColor(QPalette.AlternateBase, QColor(p["bg_surface_alt"]))
    pal.setColor(QPalette.Text, text_primary)
    pal.setColor(QPalette.Button, btn_bg)
    pal.setColor(QPalette.ButtonText, text_primary)
    pal.setColor(QPalette.Highlight, accent)
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))

    return pal


def apply_card_shadow(widget: QWidget, theme: str = "dark"):
    """Apply a subtle, modern 3D elevation drop shadow to a card widget."""
    shadow = QGraphicsDropShadowEffect(widget)
    p = DARK_PALETTE if theme == "dark" else LIGHT_PALETTE
    shadow.setColor(p["shadow_color"])
    shadow.setBlurRadius(20)
    shadow.setOffset(0, 4)
    widget.setGraphicsEffect(shadow)


def get_stylesheet(theme: str = "dark") -> str:
    """Generate modern, high-contrast Qt Stylesheet (QSS) for the given theme mode."""
    p = DARK_PALETTE if theme == "dark" else LIGHT_PALETTE

    return f"""
    /* Canvas & Global Viewport Defaults */
    QMainWindow, QDialog, QWidget#centralWidget, QStackedWidget,
    QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget,
    QWidget#scrollContainer, QWidget#setupView, QWidget#previewView, QWidget#resultsView {{
        background-color: {p["bg_main"]};
        color: {p["text_primary"]};
        font-size: 13px;
    }}

    QScrollArea {{
        border: none;
        background-color: {p["bg_main"]};
    }}

    /* Card Panels with Clean Elevation */
    QFrame.card {{
        background-color: {p["bg_surface"]};
        border: 1px solid {p["border"]};
        border-radius: 12px;
        padding: 20px;
    }}
    QFrame.card:hover {{
        border-color: {p["border_hover"]};
    }}

    /* Typography Hierarchy */
    QLabel {{
        color: {p["text_primary"]};
    }}
    QLabel.title {{
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: {p["text_primary"]};
    }}
    QLabel.subtitle {{
        font-size: 13px;
        font-weight: 400;
        color: {p["text_secondary"]};
    }}
    QLabel.section-header {{
        font-size: 15px;
        font-weight: 700;
        letter-spacing: -0.2px;
        color: {p["text_primary"]};
    }}
    QLabel.card-desc {{
        font-size: 13px;
        font-weight: 400;
        color: {p["text_secondary"]};
    }}
    QLabel.badge {{
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
        background-color: {p["badge_bg"]};
        color: {p["badge_text"]};
        border: 1px solid {p["badge_border"]};
    }}

    /* Modern Crisp Inputs */
    QLineEdit {{
        background-color: {p["input_bg"]};
        border: 1px solid {p["border_input"]};
        border-radius: 8px;
        padding: 9px 12px;
        color: {p["text_primary"]};
        selection-background-color: {p["accent"]};
        selection-color: #ffffff;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 1.5px solid {p["border_focus"]};
        background-color: {p["bg_surface"]};
    }}
    QLineEdit:disabled {{
        background-color: {p["bg_surface_alt"]};
        color: {p["text_muted"]};
        border-color: {p["border"]};
    }}

    /* Standard Interactive Buttons */
    QPushButton {{
        background-color: {p["btn_bg"]};
        border: 1px solid {p["border_input"]};
        color: {p["text_primary"]};
        border-radius: 8px;
        padding: 9px 18px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {p["btn_hover"]};
        border-color: {p["border_focus"]};
    }}
    QPushButton:pressed {{
        background-color: {p["btn_pressed"]};
    }}
    QPushButton:disabled {{
        background-color: {p["bg_surface_alt"]};
        color: {p["text_muted"]};
        border-color: {p["border"]};
    }}

    /* Primary Accent Button */
    QPushButton.primary {{
        background-color: {p["accent"]};
        color: #ffffff;
        border: 1px solid {p["accent"]};
        font-weight: 600;
        padding: 11px 26px;
        border-radius: 8px;
    }}
    QPushButton.primary:hover {{
        background-color: {p["accent_hover"]};
        border-color: {p["accent_hover"]};
    }}
    QPushButton.primary:pressed {{
        background-color: {p["accent"]};
    }}
    QPushButton.primary:disabled {{
        background-color: {p["border"]};
        color: {p["text_muted"]};
        border-color: {p["border"]};
    }}

    /* Success Affirmative Button */
    QPushButton.success {{
        background-color: {p["success"]};
        color: #ffffff;
        border: 1px solid {p["success"]};
        font-weight: 600;
        padding: 11px 26px;
        border-radius: 8px;
    }}
    QPushButton.success:hover {{
        opacity: 0.92;
    }}

    /* Refined Radio Buttons with Sharp Concentric Dot */
    QRadioButton {{
        color: {p["text_primary"]};
        font-size: 13px;
        font-weight: 500;
        spacing: 10px;
        padding: 6px 8px;
        border-radius: 8px;
    }}
    QRadioButton:hover {{
        background-color: {p["accent_subtle"]};
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 10px;
        border: 2px solid {p["radio_border"]};
        background-color: {p["bg_surface"]};
    }}
    QRadioButton::indicator:hover {{
        border-color: {p["accent"]};
    }}
    QRadioButton::indicator:checked {{
        border: 2px solid {p["accent"]};
        background: qradialgradient(
            cx: 0.5, cy: 0.5, radius: 0.5,
            fx: 0.5, fy: 0.5,
            stop: 0 {p["accent"]},
            stop: 0.50 {p["accent"]},
            stop: 0.52 {p["bg_surface"]},
            stop: 1.0 {p["bg_surface"]}
        );
    }}

    /* Checkboxes */
    QCheckBox {{
        color: {p["text_primary"]};
        spacing: 10px;
        font-size: 13px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 1.5px solid {p["radio_border"]};
        background-color: {p["bg_surface"]};
    }}
    QCheckBox::indicator:hover {{
        border-color: {p["accent"]};
    }}
    QCheckBox::indicator:checked {{
        border-color: {p["accent"]};
        background-color: {p["accent"]};
    }}

    /* Data Table View */
    QTableWidget {{
        background-color: {p["bg_surface"]};
        border: 1px solid {p["border"]};
        border-radius: 10px;
        gridline-color: transparent;
        color: {p["text_primary"]};
        selection-background-color: {p["accent_subtle"]};
        selection-color: {p["text_primary"]};
        font-size: 13px;
    }}
    QTableWidget::item {{
        padding: 9px 12px;
        border-bottom: 1px solid {p["border"]};
    }}
    QTableWidget::item:selected {{
        background-color: {p["accent_subtle"]};
    }}
    QHeaderView::section {{
        background-color: {p["bg_surface_alt"]};
        color: {p["text_secondary"]};
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 10px 12px;
        border: none;
        border-bottom: 1px solid {p["border"]};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {p["border_input"]};
        min-height: 28px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p["text_muted"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Slim Futuristic Progress Bar */
    QProgressBar {{
        background-color: {p["bg_surface_alt"]};
        border: 1px solid {p["border_input"]};
        border-radius: 6px;
        text-align: center;
        color: {p["text_primary"]};
        font-weight: 600;
        font-size: 12px;
        height: 18px;
    }}
    QProgressBar::chunk {{
        background-color: {p["accent"]};
        border-radius: 5px;
    }}

    /* ComboBox */
    QComboBox {{
        background-color: {p["input_bg"]};
        border: 1px solid {p["border_input"]};
        border-radius: 8px;
        padding: 7px 12px;
        color: {p["text_primary"]};
        font-size: 13px;
    }}
    QComboBox:hover {{
        border-color: {p["border_focus"]};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p["bg_surface"]};
        border: 1px solid {p["border_input"]};
        color: {p["text_primary"]};
        selection-background-color: {p["accent"]};
        selection-color: #ffffff;
    }}
    """
