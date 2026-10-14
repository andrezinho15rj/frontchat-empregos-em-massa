"""Página 10 — Configurações (fontes de vagas, tema, dados, exportação)."""
from __future__ import annotations

import os
import subprocess

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from ... import app_name, app_paths
from ...db.database import database
from ...db.repositories import settings_repo
from ...export import exporter
from ...search import ALL_SOURCES
from .base import PageBase


class SettingsPage(PageBase):
    title = "Configurações"
    subtitle = "Fontes de vagas, aparência, exportação e gerenciamento de dados."

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)
        scroll_host = QWidget()
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)

        # --- Fontes de vagas (todas sem chave de API) ---
        api = QGroupBox("Fontes de vagas (nenhuma exige chave de API)")
        f = QVBoxLayout(api)
        info_src = QLabel(
            "Estas fontes funcionam automaticamente, sem cadastro nem chave. "
            "É necessária apenas conexão com a internet:")
        info_src.setWordWrap(True)
        info_src.setObjectName("Muted")
        f.addWidget(info_src)
        for src in ALL_SOURCES:
            item = QLabel(f"•  {src.name} — {src.description}")
            item.setWordWrap(True)
            f.addWidget(item)
        layout.addWidget(api)

        # --- Aparência ---
        app_box = QGroupBox("Aparência")
        af = QFormLayout(app_box)
        self.theme = QComboBox()
        self.theme.addItems(["Escuro", "Claro"])
        self.theme.setCurrentText("Escuro" if settings_repo.get_bool("dark_theme", True) else "Claro")
        self.theme.currentTextChanged.connect(self.apply_theme)
        af.addRow("Tema", self.theme)
        layout.addWidget(app_box)

        # --- Exportação ---
        exp = QGroupBox("Exportação de dados")
        ef = QFormLayout(exp)
        self.exp_search = QLineEdit()
        self.exp_area = QLineEdit()
        self.exp_status = QComboBox()
        self.exp_status.addItems(["", "Preparada", "Enviada", "Falha no envio"])
        self.exp_only_email = QCheckBox("Somente registros com e-mail")
        ef.addRow("Filtrar por texto", self.exp_search)
        ef.addRow("Área", self.exp_area)
        ef.addRow("Status candidatura", self.exp_status)
        ef.addRow("", self.exp_only_email)
        row = QHBoxLayout()
        csv_btn = QPushButton("Exportar CSV")
        csv_btn.clicked.connect(lambda: self.do_export("csv"))
        xlsx_btn = QPushButton("Exportar Excel (.xlsx)")
        xlsx_btn.setObjectName("Primary")
        xlsx_btn.clicked.connect(lambda: self.do_export("xlsx"))
        row.addWidget(csv_btn)
        row.addWidget(xlsx_btn)
        holder = QWidget()
        holder.setLayout(row)
        ef.addRow("", holder)
        self.preview_lbl = QLabel("")
        self.preview_lbl.setObjectName("Muted")
        ef.addRow("", self.preview_lbl)
        layout.addWidget(exp)

        # --- Dados e privacidade ---
        data_box = QGroupBox("Dados e privacidade (LGPD)")
        df = QVBoxLayout(data_box)
        info = QLabel(f"Dados armazenados em:\n{app_paths.data_dir()}")
        info.setWordWrap(True)
        info.setObjectName("Muted")
        df.addWidget(info)
        row2 = QHBoxLayout()
        open_btn = QPushButton("Abrir pasta de dados")
        open_btn.clicked.connect(self.open_data_dir)
        del_btn = QPushButton("Excluir permanentemente todos os dados")
        del_btn.setObjectName("Danger")
        del_btn.clicked.connect(self.wipe_data)
        row2.addWidget(open_btn)
        row2.addWidget(del_btn)
        row2.addStretch()
        df.addLayout(row2)
        layout.addWidget(data_box)

        about = QLabel(f"{app_name} — prospecção de vagas e candidaturas.\n"
                       "Os dados coletados são públicos e mantidos localmente.")
        about.setObjectName("Muted")
        about.setWordWrap(True)
        layout.addWidget(about)

        layout.addStretch()
        scroll.setWidget(inner)
        self.root.addWidget(scroll)

    def apply_theme(self, value: str) -> None:
        dark = value == "Escuro"
        settings_repo.set("dark_theme", "1" if dark else "0")
        if self.app_window:
            self.app_window.apply_theme(dark)

    def do_export(self, fmt: str) -> None:
        rows = exporter.preview(
            status_filter=self.exp_status.currentText(),
            area_filter=self.exp_area.text().strip(),
            search=self.exp_search.text().strip(),
            only_with_email=self.exp_only_email.isChecked(),
        )
        if not rows:
            self.toast("Nenhum registro para exportar com esses filtros.", "warning")
            return
        ext = "csv" if fmt == "csv" else "xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar exportação", str(app_paths.exports_dir() / f"jobhunter.{ext}"),
            "CSV (*.csv)" if fmt == "csv" else "Excel (*.xlsx)")
        if not path:
            return
        try:
            written = exporter.to_csv(rows, path) if fmt == "csv" else exporter.to_xlsx(rows, path)
            self.preview_lbl.setText(f"Exportados {len(rows)} registros para {written}")
            self.toast(f"Exportação concluída: {len(rows)} registros.", "success")
        except Exception as exc:
            self.toast(f"Falha na exportação: {exc}", "error")

    def open_data_dir(self) -> None:
        try:
            os.startfile(str(app_paths.data_dir()))  # noqa: S606
        except Exception:
            subprocess.Popen(["explorer", str(app_paths.data_dir())])

    def wipe_data(self) -> None:
        reply = QMessageBox.warning(
            self, "Excluir dados",
            "Isto apaga PERMANENTEMENTE empresas, vagas, contatos, currículos e "
            "histórico de candidaturas.\nDeseja continuar?",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        database.wipe_all()
        self.toast("Todos os dados locais foram apagados.", "success")
