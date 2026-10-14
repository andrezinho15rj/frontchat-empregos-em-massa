"""Página 3 — Empresas encontradas."""
from __future__ import annotations

import webbrowser

from PySide6.QtWidgets import (
    QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout,
)

from ...db.repositories import company_repo
from ..widgets import add_row, make_table
from ..workers import Worker
from .base import PageBase


class CompaniesPage(PageBase):
    title = "Empresas encontradas"
    subtitle = "Empresas identificadas a partir das vagas e da descoberta de contatos."

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filtrar por nome, domínio ou local...")
        self.search.textChanged.connect(self.load)
        bar.addWidget(self.search)
        btn = QPushButton("Buscar contatos")
        btn.setObjectName("Primary")
        btn.clicked.connect(self.discover)
        bar.addWidget(btn)
        open_btn = QPushButton("Abrir site")
        open_btn.clicked.connect(self.open_site)
        bar.addWidget(open_btn)
        self.root.addLayout(bar)

        self.table = make_table([
            ("name", "Empresa"), ("domain", "Domínio"), ("website", "Site"),
            ("location", "Local"), ("careers", "Página de carreiras"),
        ], stretch_col=2)
        self.root.addWidget(self.table)
        self.load()

    def load(self) -> None:
        self.table.setRowCount(0)
        for c in company_repo.list(search=self.search.text().strip()):
            add_row(self.table, [
                c["name"], c["domain"] or "—", c["website"] or "—",
                c["location"] or "—", c["careers_url"] or "—",
            ], user_data=c["id"])

    def _selected_company_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return self.table.item(items[0].row(), 0).data(0x0100)  # Qt.UserRole

    def discover(self) -> None:
        cid = self._selected_company_id()
        if not cid:
            self.toast("Selecione uma empresa.", "warning")
            return
        self.worker = Worker(self._run_discover, cid)
        self.worker.finished_ok.connect(self._done)
        self.worker.failed.connect(lambda e: self.toast(e.splitlines()[0], "error"))
        self.toast("Buscando contatos públicos...", "info")
        self.worker.start()

    def _run_discover(self, cid):
        from ...contacts import contact_discovery
        return contact_discovery.process_company(cid)

    def _done(self, report) -> None:
        self.toast(f"{report.emails_saved} contatos salvos, "
                   f"{report.forms_found} formulários.", "success")
        self.load()

    def open_site(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        website = self.table.item(row, 2).text()
        if website and website != "—":
            webbrowser.open(website)

    def on_show(self) -> None:
        self.load()
