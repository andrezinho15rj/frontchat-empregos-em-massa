"""Página 4 — Contatos de recrutamento."""
from __future__ import annotations

import webbrowser

from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout,
)

from ...db.repositories import contact_repo
from ..widgets import add_row, make_table, status_item
from .base import PageBase


class ContactsPage(PageBase):
    title = "Contatos de recrutamento"
    subtitle = "E-mails e formulários públicos com origem e status de verificação."

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filtrar por e-mail, telefone, empresa ou domínio...")
        self.search.textChanged.connect(self.load)
        bar.addWidget(self.search)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos os status", "")
        for st in [
            "Encontrado e origem confirmada",
            "Domínio válido, entrega não confirmada",
            "Telefone encontrado",
            "Formulário de candidatura disponível",
            "E-mail duplicado",
            "Contato inadequado para candidatura",
            "E-mail inválido",
        ]:
            self.status_filter.addItem(st, st)
        self.status_filter.currentIndexChanged.connect(self.load)
        bar.addWidget(self.status_filter)
        open_btn = QPushButton("Abrir origem")
        open_btn.clicked.connect(self.open_source)
        bar.addWidget(open_btn)
        self.root.addLayout(bar)

        self.table = make_table([
            ("email", "E-mail"), ("phone", "Telefone"), ("form", "Formulário"),
            ("company", "Empresa"), ("domain", "Domínio"), ("category", "Categoria"),
            ("status", "Status"), ("source", "Fonte"), ("checked", "Verificado em"),
        ], stretch_col=7)
        self.root.addWidget(self.table)
        self.load()

    def load(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for c in contact_repo.list(search=self.search.text().strip(),
                                   status=self.status_filter.currentData() or ""):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, _it(c["email"] or "—"))
            self.table.setItem(row, 1, _it(c["phone"] or "—"))
            self.table.setItem(row, 2, _it(c["form_url"] or "—"))
            self.table.setItem(row, 3, _it(c["company_name"] or "—"))
            self.table.setItem(row, 4, _it(c["domain"] or "—"))
            self.table.setItem(row, 5, _it(c["category"] or "—"))
            self.table.setItem(row, 6, status_item(c["status"] or ""))
            self.table.setItem(row, 7, _it(c["source_url"] or "—"))
            self.table.setItem(row, 8, _it((c["checked_at"] or "")[:16]))
            self.table.item(row, 0).setData(0x0100, c["id"])
        self.table.setSortingEnabled(True)

    def open_source(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        url = self.table.item(row, 7).text()
        if url and url != "—":
            webbrowser.open(url)

    def on_show(self) -> None:
        self.load()


def _it(text):
    from PySide6.QtWidgets import QTableWidgetItem
    return QTableWidgetItem(str(text) if text is not None else "")
