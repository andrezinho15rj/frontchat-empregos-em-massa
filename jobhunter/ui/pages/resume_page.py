"""Página 6 — Meu currículo."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout,
)

from ...db.repositories import resume_repo
from ...resume import import_resume
from ..widgets import add_row, make_table
from ..workers import Worker
from .base import PageBase


class ResumePage(PageBase):
    title = "Meu currículo"
    subtitle = "Importe seu currículo em PDF ou DOCX. O texto é extraído para personalização."

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)
        bar = QHBoxLayout()
        imp = QPushButton("Importar currículo (PDF/DOCX)")
        imp.setObjectName("Primary")
        imp.clicked.connect(self.import_file)
        use = QPushButton("Definir como ativo")
        use.clicked.connect(self.set_active)
        bar.addWidget(imp)
        bar.addWidget(use)
        bar.addStretch()
        self.root.addLayout(bar)

        self.table = make_table([
            ("name", "Nome"), ("type", "Tipo"), ("active", "Ativo"),
            ("chars", "Caracteres"), ("imported", "Importado em"),
        ], stretch_col=0)
        self.table.itemSelectionChanged.connect(self.show_selected)
        self.root.addWidget(self.table)

        self.root.addWidget(QLabel("Pré-visualização do texto extraído"))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.root.addWidget(self.preview)
        self.load()

    def load(self) -> None:
        self.table.setRowCount(0)
        for r in resume_repo.list():
            add_row(self.table, [
                r["name"], (r["file_type"] or "").upper(),
                "Sim" if r["is_active"] else "—",
                len(r["content_text"] or ""), (r["imported_at"] or "")[:16],
            ], user_data=r["id"])

    def import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar currículo", "",
            "Currículos (*.pdf *.docx *.doc *.txt)")
        if not path:
            return
        self.worker = Worker(import_resume, path)
        self.worker.finished_ok.connect(self._imported)
        self.worker.failed.connect(lambda e: self.toast(e.splitlines()[0], "error"))
        self.worker.start()

    def _imported(self, result) -> None:
        rid, text, ftype = result
        self.toast(f"Currículo importado ({ftype}, {len(text)} caracteres).", "success")
        self.load()

    def _selected_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return self.table.item(items[0].row(), 0).data(0x0100)

    def set_active(self) -> None:
        rid = self._selected_id()
        if not rid:
            self.toast("Selecione um currículo.", "warning")
            return
        resume_repo.set_active(rid)
        self.toast("Currículo ativo atualizado.", "success")
        self.load()

    def show_selected(self) -> None:
        rid = self._selected_id()
        if not rid:
            self.preview.clear()
            return
        r = resume_repo.get(rid)
        self.preview.setPlainText((r["content_text"] or "")[:20000])

    def on_show(self) -> None:
        self.load()
