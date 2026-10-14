"""Classe base para as páginas da aplicação."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PageBase(QWidget):
    title = "Página"
    subtitle = ""

    def __init__(self, app_window=None, parent=None):
        super().__init__(parent)
        self.app_window = app_window
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(24, 20, 24, 20)
        self.root.setSpacing(16)

        header = QVBoxLayout()
        header.setSpacing(2)
        self.title_lbl = QLabel(self.title)
        self.title_lbl.setObjectName("PageTitle")
        header.addWidget(self.title_lbl)
        if self.subtitle:
            sub = QLabel(self.subtitle)
            sub.setObjectName("PageSubtitle")
            header.addWidget(sub)
        self.root.addLayout(header)

    def toast(self, text: str, level: str = "info") -> None:
        if self.app_window and hasattr(self.app_window, "toast"):
            self.app_window.toast(text, level)

    def on_show(self) -> None:
        """Chamado quando a página é exibida. Sobrescrever quando necessário."""
