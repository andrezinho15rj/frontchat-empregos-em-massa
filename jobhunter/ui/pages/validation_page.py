"""Página 5 — Validação de e-mails."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QProgressBar, QPushButton, QTableWidget,
)

from ...db.repositories import contact_repo
from ...validation import dns_available, mark_duplicates, validate_email
from ..widgets import make_table, status_item
from ..workers import Worker
from .base import PageBase


class ValidationPage(PageBase):
    title = "Validação de e-mails"
    subtitle = ("Sintaxe, domínio e registros MX. MX não confirma a existência "
                "de uma caixa postal.")

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)
        bar = QHBoxLayout()
        self.revalidate_btn = QPushButton("Revalidar contatos")
        self.revalidate_btn.setObjectName("Primary")
        self.revalidate_btn.clicked.connect(self.revalidate)
        self.dedup_btn = QPushButton("Marcar duplicados")
        self.dedup_btn.clicked.connect(self.dedup)
        bar.addWidget(self.revalidate_btn)
        bar.addWidget(self.dedup_btn)
        bar.addStretch()
        self.dns_lbl = QLabel("DNS disponível" if dns_available()
                              else "DNS indisponível — MX não será verificado")
        self.dns_lbl.setObjectName("Muted")
        bar.addWidget(self.dns_lbl)
        self.root.addLayout(bar)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.root.addWidget(self.progress)

        self.table = make_table([
            ("email", "E-mail"), ("domain", "Domínio"), ("syntax", "Sintaxe"),
            ("mx", "MX"), ("category", "Categoria"), ("status", "Status"),
            ("checked", "Verificado em"),
        ], stretch_col=0)
        self.root.addWidget(self.table)
        self.load()

    def load(self) -> None:
        self.table.setRowCount(0)
        from PySide6.QtWidgets import QTableWidgetItem
        for c in contact_repo.list(limit=5000):
            if not c["email"]:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(c["email"] or ""))
            self.table.setItem(row, 1, QTableWidgetItem(c["domain"] or ""))
            self.table.setItem(row, 2, QTableWidgetItem("OK" if c["syntax_ok"] else "—"))
            self.table.setItem(row, 3, QTableWidgetItem("OK" if c["mx_ok"] else "—"))
            self.table.setItem(row, 4, QTableWidgetItem(c["category"] or ""))
            self.table.setItem(row, 5, status_item(c["status"] or ""))
            self.table.setItem(row, 6, QTableWidgetItem((c["checked_at"] or "")[:16]))

    def revalidate(self) -> None:
        rows = [c for c in contact_repo.list(limit=5000) if c["email"]]
        if not rows:
            self.toast("Nenhum contato para validar.", "warning")
            return
        self.revalidate_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(rows))
        self.worker = Worker(self._do_validate, rows, with_progress=True)
        self.worker.progress.connect(lambda c, t, m: self.progress.setValue(c))
        self.worker.finished_ok.connect(self._done)
        self.worker.failed.connect(lambda e: self.toast(e.splitlines()[0], "error"))
        self.worker.start()

    def _do_validate(self, rows, progress=None):
        for i, c in enumerate(rows):
            if progress:
                progress(i + 1, len(rows), "")
            origin_confirmed = bool(c["source_url"])
            res = validate_email(c["email"], check_mx=dns_available(),
                                 origin_confirmed=origin_confirmed)
            contact_repo.update(
                c["id"], status=res.status.value, syntax_ok=1 if res.syntax_ok else 0,
                mx_ok=1 if res.mx_ok else 0, category=res.category or c["category"],
                checked_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        mark_duplicates()
        return len(rows)

    def _done(self, count) -> None:
        self.revalidate_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.toast(f"{count} contatos revalidados.", "success")
        self.load()

    def dedup(self) -> None:
        n = mark_duplicates()
        self.toast(f"{n} contatos marcados como duplicados.", "info")
        self.load()

    def on_show(self) -> None:
        self.load()
