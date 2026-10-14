"""Janela principal com menu lateral e navegação entre as 10 telas."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
)

from .. import __version__, app_name
from ..db.repositories import settings_repo
from . import theme
from .pages import (
    AIPage, CampaignsPage, CompaniesPage, ContactsPage, DashboardPage,
    HistoryPage, ResumePage, SearchJobsPage, SettingsPage, ValidationPage,
)
from .widgets import Toast

NAV_ITEMS = [
    ("Dashboard", "📊", DashboardPage),
    ("Buscar vagas", "🔎", SearchJobsPage),
    ("Empresas encontradas", "🏢", CompaniesPage),
    ("Contatos de recrutamento", "✉", ContactsPage),
    ("Validação de e-mails", "✔", ValidationPage),
    ("Meu currículo", "📄", ResumePage),
    ("Inteligência artificial", "🤖", AIPage),
    ("Campanhas de candidatura", "🚀", CampaignsPage),
    ("Histórico de envios", "🕑", HistoryPage),
    ("Configurações", "⚙", SettingsPage),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{app_name} {__version__}")
        self.resize(1360, 860)
        self.setMinimumSize(1100, 700)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(252)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(14, 20, 14, 18)
        sl.setSpacing(6)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        mark = QLabel("F")
        mark.setObjectName("BrandMark")
        mark.setFixedSize(38, 38)
        mark.setAlignment(Qt.AlignCenter)
        brand_row.addWidget(mark)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand = QLabel("Frontchat")
        brand.setObjectName("Brand")
        sub = QLabel("Empregos em Massa")
        sub.setObjectName("BrandSub")
        brand_text.addWidget(brand)
        brand_text.addWidget(sub)
        brand_row.addLayout(brand_text)
        brand_row.addStretch()
        sl.addLayout(brand_row)
        sl.addSpacing(18)

        self.stack = QStackedWidget()
        self.nav_buttons: list[QPushButton] = []
        self.pages: list = []
        group = QButtonGroup(self)
        group.setExclusive(True)
        section_added = False
        for idx, (label, icon, cls) in enumerate(NAV_ITEMS):
            if idx == 1 and not section_added:
                sec = QLabel("PROSPECÇÃO")
                sec.setObjectName("NavSection")
                sl.addWidget(sec)
                section_added = True
            elif idx == 7:
                sec = QLabel("CANDIDATURAS")
                sec.setObjectName("NavSection")
                sl.addWidget(sec)
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, i=idx: self.goto(i))
            group.addButton(btn, idx)
            sl.addWidget(btn)
            self.nav_buttons.append(btn)

            page = cls(app_window=self)
            self.pages.append(page)
            self.stack.addWidget(page)

        sl.addStretch()
        footer = QLabel(f"v{__version__}  •  Dados locais  •  LGPD")
        footer.setObjectName("BrandSub")
        footer.setAlignment(Qt.AlignCenter)
        sl.addWidget(footer)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)

        # Toast overlay
        self.toast_widget = Toast(root)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Pronto.")

        self.nav_buttons[0].setChecked(True)
        self.goto(0)
        self.apply_theme(settings_repo.get_bool("dark_theme", True))

    def goto(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.nav_buttons[index].setChecked(True)
        page = self.pages[index]
        try:
            page.on_show()
        except Exception as exc:  # pragma: no cover
            self.toast(f"Erro ao abrir tela: {exc}", "error")

    def toast(self, message: str, level: str = "info") -> None:
        self.toast_widget.parentWidget()  # ensure parent
        self.toast_widget.show_message(message, level)
        self.statusBar().showMessage(message, 6000)

    def apply_theme(self, dark: bool) -> None:
        self.setStyleSheet(theme.stylesheet(dark))

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        if self.toast_widget.isVisible():
            self.toast_widget._reposition()
