"""Página 9 — Histórico de envios."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout,
)

from ...db.repositories import application_repo
from ..widgets import make_table, status_item
from .base import PageBase


class HistoryPage(PageBase):
    title = "Histórico de envios"
    subtitle = "Registro de cada tentativa com data, hora e resultado do provedor."

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filtrar por empresa, e-mail ou assunto…")
        self.search.textChanged.connect(self.load)
        bar.addWidget(self.search)
        self.status = QComboBox()
        self.status.addItems(["Todas", "Preparada", "Enviada", "Falha no envio",
                              "Resposta recebida", "Entrevista", "Cancelada"])
        self.status.currentIndexChanged.connect(self.load)
        bar.addWidget(self.status)
        mark_reply = QPushButton("Marcar como resposta recebida")
        mark_reply.clicked.connect(lambda: self._mark("Resposta recebida"))
        mark_interview = QPushButton("Marcar entrevista")
        mark_interview.clicked.connect(lambda: self._mark("Entrevista"))
        bar.addWidget(mark_reply)
        bar.addWidget(mark_interview)
        self.root.addLayout(bar)

        self.table = make_table([
            ("company", "Empresa"), ("job", "Vaga"), ("email", "E-mail"),
            ("subject", "Assunto"), ("status", "Status"),
            ("prepared", "Preparada em"), ("sent", "Enviada em"), ("error", "Erro"),
        ], stretch_col=3)
        self.root.addWidget(self.table)
        self.load()

    def load(self) -> None:
        status = self.status.currentText()
        status = "" if status == "Todas" else status
        self.table.setRowCount(0)
        for a in application_repo.list(status=status, search=self.search.text().strip()):
            r = self.table.rowCount()
            self.table.insertRow(r)
            from PySide6.QtWidgets import QTableWidgetItem
            self.table.setItem(r, 0, QTableWidgetItem(a["company_name"] or "—"))
            self.table.setItem(r, 1, QTableWidgetItem(a["job_title"] or "—"))
            self.table.setItem(r, 2, QTableWidgetItem(a["to_email"] or ""))
            self.table.setItem(r, 3, QTableWidgetItem(a["subject"] or ""))
            self.table.setItem(r, 4, status_item(a["status"] or ""))
            self.table.setItem(r, 5, QTableWidgetItem((a["prepared_at"] or "")[:16]))
            self.table.setItem(r, 6, QTableWidgetItem((a["sent_at"] or "")[:16]))
            self.table.setItem(r, 7, QTableWidgetItem((a["error"] or "")[:60]))
            self.table.item(r, 0).setData(0x0100, a["id"])

    def _mark(self, status: str) -> None:
        items = self.table.selectedItems()
        if not items:
            self.toast("Selecione um registro.", "warning")
            return
        for it in items:
            if it.column() != 0:
                continue
            aid = self.table.item(it.row(), 0).data(0x0100)
            application_repo.update(aid, status=status)
        self.toast(f"Status atualizado: {status}.", "success")
        self.load()

    def on_show(self) -> None:
        self.load()
