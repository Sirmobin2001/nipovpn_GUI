"""Modern dark theme (Qt style sheet) for the NipoVPN GUI."""

from __future__ import annotations

# Color palette
COLORS = {
    "bg": "#0f1419",
    "surface": "#1a2129",
    "surface_alt": "#222c37",
    "border": "#2c3947",
    "text": "#e6edf3",
    "text_muted": "#8b98a5",
    "accent": "#3b82f6",
    "accent_hover": "#2f6fd6",
    "success": "#22c55e",
    "danger": "#ef4444",
    "warning": "#f59e0b",
}

STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Roboto", "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 14px;
    color: {COLORS['text']};
    outline: none;
}}

QWidget#root {{
    background-color: {COLORS['bg']};
}}

/* Sidebar */
QWidget#sidebar {{
    background-color: {COLORS['surface']};
    border-right: 1px solid {COLORS['border']};
}}

QLabel#brand {{
    font-size: 20px;
    font-weight: 700;
    color: {COLORS['text']};
    padding: 4px 0;
}}

QLabel#brandAccent {{
    color: {COLORS['accent']};
}}

QPushButton#navButton {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    color: {COLORS['text_muted']};
    font-weight: 600;
}}

QPushButton#navButton:hover {{
    background-color: {COLORS['surface_alt']};
    color: {COLORS['text']};
}}

QPushButton#navButton:checked {{
    background-color: {COLORS['accent']};
    color: #ffffff;
}}

/* Cards */
QFrame#card {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}

QLabel#cardTitle {{
    font-size: 13px;
    font-weight: 700;
    color: {COLORS['text_muted']};
    text-transform: uppercase;
    letter-spacing: 1px;
}}

QLabel#statValue {{
    font-size: 26px;
    font-weight: 700;
    color: {COLORS['text']};
}}

QLabel#statLabel {{
    font-size: 12px;
    color: {COLORS['text_muted']};
}}

QLabel#sectionTitle {{
    font-size: 18px;
    font-weight: 700;
}}

QLabel#hint {{
    color: {COLORS['text_muted']};
    font-size: 12px;
}}

/* Inputs */
QLineEdit, QSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
    background-color: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: {COLORS['accent']};
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus,
QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {COLORS['accent']};
}}

QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background-color: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent']};
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
}}

QPushButton:hover {{ background-color: {COLORS['border']}; }}
QPushButton:disabled {{ color: {COLORS['text_muted']}; }}

QPushButton#primary {{
    background-color: {COLORS['accent']};
    border: none;
    color: #ffffff;
}}
QPushButton#primary:hover {{ background-color: {COLORS['accent_hover']}; }}

QPushButton#danger {{
    background-color: {COLORS['danger']};
    border: none;
    color: #ffffff;
}}
QPushButton#danger:hover {{ background-color: #d63b3b; }}

QPushButton#connect {{
    border-radius: 60px;
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
    background-color: {COLORS['accent']};
    border: none;
}}
QPushButton#connect:hover {{ background-color: {COLORS['accent_hover']}; }}
QPushButton#connect[connected="true"] {{ background-color: {COLORS['danger']}; }}
QPushButton#connect[connected="true"]:hover {{ background-color: #d63b3b; }}

/* Log console */
QPlainTextEdit#console {{
    background-color: #0b0f14;
    font-family: "JetBrains Mono", "Consolas", "DejaVu Sans Mono", monospace;
    font-size: 12px;
    color: #c7d1db;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']}; border-radius: 5px; min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 4px;
    border: 1px solid {COLORS['border']};
    background: {COLORS['surface_alt']};
}}
QCheckBox::indicator:checked {{
    background: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
}}
"""
