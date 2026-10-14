"""Temas claro/escuro (QSS) e paletas de cores — visual SaaS premium."""
from __future__ import annotations

ACCENT = "#4C7DFF"
ACCENT_2 = "#7C5CFF"
ACCENT_DARK = "#3A66DB"

DARK = {
    "bg": "#0B0F17",
    "surface": "#141A24",
    "surface2": "#1B2431",
    "surface3": "#222D3D",
    "border": "#28313F",
    "text": "#EAF0FB",
    "muted": "#8C9AB2",
    "accent": ACCENT,
    "accent2": ACCENT_2,
    "success": "#24C08A",
    "warning": "#F0A73C",
    "danger": "#F2584C",
    "sidebar": "#0F1520",
}

LIGHT = {
    "bg": "#F1F4FA",
    "surface": "#FFFFFF",
    "surface2": "#EBF0F9",
    "surface3": "#E0E7F3",
    "border": "#DCE3EF",
    "text": "#16233A",
    "muted": "#64748B",
    "accent": ACCENT,
    "accent2": ACCENT_2,
    "success": "#12996A",
    "warning": "#C9821A",
    "danger": "#DA3B30",
    "sidebar": "#111A2B",
}


def palette(dark: bool) -> dict:
    return DARK if dark else LIGHT


def stylesheet(dark: bool = True) -> str:
    c = palette(dark)
    return f"""
    * {{
        font-family: "Segoe UI Variable", "Segoe UI", "Inter", Arial, sans-serif;
        font-size: 13px;
        color: {c['text']};
        outline: none;
    }}
    QMainWindow, QWidget#Root {{ background: {c['bg']}; }}

    /* ---------- Sidebar ---------- */
    QWidget#Sidebar {{
        background: {c['sidebar']};
        border-right: 1px solid {c['border']};
    }}
    QLabel#Brand {{ font-size: 17px; font-weight: 800; color: #FFFFFF; letter-spacing: .3px; }}
    QLabel#BrandSub {{ font-size: 10.5px; color: {c['muted']}; }}
    QLabel#BrandMark {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {c['accent']}, stop:1 {c['accent2']});
        border-radius: 12px; color: white; font-size: 18px; font-weight: 800;
    }}
    QLabel#NavSection {{ color: {c['muted']}; font-size: 10px; font-weight: 700;
        letter-spacing: 1.2px; padding: 4px 12px; }}

    QPushButton#NavButton {{
        text-align: left; padding: 10px 14px; border: none; border-radius: 10px;
        background: transparent; color: #A9B6CC; font-weight: 500;
    }}
    QPushButton#NavButton:hover {{ background: rgba(255,255,255,0.06); color: #FFFFFF; }}
    QPushButton#NavButton:checked {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['accent']}, stop:1 {c['accent2']});
        color: #FFFFFF; font-weight: 700;
    }}

    /* ---------- Cabeçalhos ---------- */
    QLabel#PageTitle {{ font-size: 24px; font-weight: 800; letter-spacing: .2px; }}
    QLabel#PageSubtitle {{ color: {c['muted']}; font-size: 12.5px; }}
    QLabel#SectionTitle {{ font-size: 15px; font-weight: 700; }}
    QLabel#Muted {{ color: {c['muted']}; }}

    /* ---------- Botões ---------- */
    QPushButton {{
        background: {c['surface2']}; border: 1px solid {c['border']};
        border-radius: 9px; padding: 8px 16px; color: {c['text']}; font-weight: 600;
    }}
    QPushButton:hover {{ background: {c['surface3']}; border-color: {c['accent']}; }}
    QPushButton:pressed {{ padding-top: 9px; padding-bottom: 7px; }}
    QPushButton#Primary {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['accent']}, stop:1 {c['accent2']});
        border: none; color: #FFFFFF; font-weight: 700;
    }}
    QPushButton#Primary:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_DARK}, stop:1 {c['accent']});
    }}
    QPushButton#Success {{ background: {c['success']}; border: none; color: #FFFFFF; font-weight: 700; }}
    QPushButton#Warning {{ background: {c['warning']}; border: none; color: #FFFFFF; font-weight: 700; }}
    QPushButton#Danger {{ background: {c['danger']}; border: none; color: #FFFFFF; font-weight: 700; }}
    QPushButton:disabled {{ background: {c['surface2']}; color: {c['muted']}; border-color: {c['border']}; }}

    /* ---------- Entradas ---------- */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QDateEdit {{
        background: {c['surface']}; border: 1.5px solid {c['border']};
        border-radius: 9px; padding: 8px 11px; selection-background-color: {c['accent']};
        selection-color: #FFFFFF;
    }}
    QLineEdit:hover, QComboBox:hover, QTextEdit:hover, QPlainTextEdit:hover {{
        border-color: {c['surface3']};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
    QTextEdit:focus, QPlainTextEdit:focus, QDateEdit:focus {{
        border-color: {c['accent']};
    }}
    QComboBox::drop-down {{ border: none; width: 26px; }}
    QComboBox::down-arrow {{
        image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
        border-top: 5px solid {c['muted']}; margin-right: 10px;
    }}
    QComboBox QAbstractItemView {{
        background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 8px;
        selection-background-color: {c['accent']}; selection-color: #FFFFFF; padding: 4px;
    }}

    /* ---------- Tabelas ---------- */
    QTableWidget, QTableView {{
        background: {c['surface']}; border: 1px solid {c['border']};
        border-radius: 14px; gridline-color: transparent;
        selection-background-color: {c['surface3']}; selection-color: {c['text']};
        alternate-background-color: {c['surface']};
    }}
    QTableWidget::item, QTableView::item {{ padding: 6px 8px; border-bottom: 1px solid {c['border']}; }}
    QTableWidget::item:selected, QTableView::item:selected {{ background: {c['surface3']}; }}
    QHeaderView::section {{
        background: {c['surface2']}; border: none; padding: 10px 8px;
        font-weight: 700; color: {c['muted']}; border-bottom: 1px solid {c['border']};
    }}
    QHeaderView::section:first {{ border-top-left-radius: 12px; }}
    QHeaderView::section:last {{ border-top-right-radius: 12px; }}
    QTableCornerButton::section {{ background: {c['surface2']}; border: none; }}

    /* ---------- Cartões ---------- */
    QFrame#Card, QFrame#MetricCard {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['surface']}, stop:1 {c['surface2']});
        border: 1px solid {c['border']}; border-radius: 16px;
    }}
    QFrame#MetricCard:hover {{ border-color: {c['accent']}; }}
    QLabel#MetricValue {{ font-size: 28px; font-weight: 800; }}
    QLabel#MetricLabel {{ color: {c['muted']}; font-size: 11.5px; font-weight: 600; }}

    /* ---------- Progresso ---------- */
    QProgressBar {{
        background: {c['surface2']}; border: none; border-radius: 8px;
        text-align: center; height: 18px; color: {c['text']}; font-weight: 600;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['accent']}, stop:1 {c['accent2']}); border-radius: 8px;
    }}

    /* ---------- Scroll bars ---------- */
    QScrollBar:vertical {{ background: transparent; width: 11px; margin: 3px; }}
    QScrollBar::handle:vertical {{ background: {c['surface3']}; border-radius: 5px; min-height: 34px; }}
    QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
    QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 3px; }}
    QScrollBar::handle:horizontal {{ background: {c['surface3']}; border-radius: 5px; min-width: 34px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

    /* ---------- Abas ---------- */
    QTabWidget::pane {{ border: 1px solid {c['border']}; border-radius: 12px; background: {c['surface']}; top: -1px; }}
    QTabBar::tab {{
        background: transparent; padding: 9px 18px; margin-right: 4px;
        color: {c['muted']}; font-weight: 600; border-radius: 9px;
    }}
    QTabBar::tab:hover {{ color: {c['text']}; background: {c['surface2']}; }}
    QTabBar::tab:selected {{
        color: #FFFFFF; border: none;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['accent']}, stop:1 {c['accent2']});
    }}

    /* ---------- Diversos ---------- */
    QCheckBox {{ spacing: 8px; }}
    QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px;
        border: 1.5px solid {c['border']}; background: {c['surface']}; }}
    QCheckBox::indicator:checked {{ background: {c['accent']}; border-color: {c['accent']}; }}
    QGroupBox {{
        border: 1px solid {c['border']}; border-radius: 14px; margin-top: 14px;
        padding: 14px 12px 10px 12px; background: {c['surface']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 14px; padding: 0 6px;
        color: {c['muted']}; font-weight: 700;
    }}
    QSplitter::handle {{ background: transparent; width: 8px; }}

    QStatusBar {{ background: {c['surface']}; color: {c['muted']};
        border-top: 1px solid {c['border']}; }}
    QToolTip {{
        background: {c['surface3']}; color: {c['text']};
        border: 1px solid {c['border']}; border-radius: 8px; padding: 6px 8px;
    }}
    """
