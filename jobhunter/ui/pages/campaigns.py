"""Página 8 — Campanhas de candidatura.

Fluxo: preparar (gera e persiste) -> revisar (editar) -> enviar (com confirmação
real do provedor). Nada é enviado sem ação explícita do usuário.
"""
from __future__ import annotations

import threading

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
    QTabWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ...campaigns import (
    PRESETS, SmtpProvider, build_values, campaign_engine, default_templates,
    render,
)
from ...db.repositories import (
    application_repo, campaign_repo, contact_repo, resume_repo, settings_repo,
)
from ...security.credentials import get_secret
from ..widgets import add_row, make_table, status_item
from ..workers import Worker
from .base import PageBase


class CampaignsPage(PageBase):
    title = "Campanhas de candidatura"
    subtitle = "Prepare, revise e envie candidaturas — sempre com aprovação manual."

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self.campaign_id: int | None = None

        splitter = QSplitter(Qt.Horizontal)

        # ---- Configuração ----
        left = QWidget()
        lv = QVBoxLayout(left)
        box = QGroupBox("Configuração da campanha")
        form = QFormLayout(box)
        self.name = QLineEdit("Campanha " + __import__("datetime").datetime.now().strftime("%d/%m %H:%M"))
        self.resume = QComboBox()
        self.language = QComboBox()
        self.language.addItems(["pt (Português)", "en (English)"])
        self.from_email = QLineEdit(settings_repo.get("smtp_from", ""))
        self.subject = QLineEdit()
        self.body = QPlainTextEdit()
        self.body.setMinimumHeight(180)
        self.use_ai = QCheckBox("Usar IA para personalizar (se configurada)")
        form.addRow("Nome", self.name)
        form.addRow("Currículo", self.resume)
        form.addRow("Idioma", self.language)
        form.addRow("Remetente", self.from_email)
        form.addRow("Assunto (modelo)", self.subject)
        form.addRow("Corpo (modelo)", self.body)
        form.addRow("", self.use_ai)
        vars_lbl = QLabel("Variáveis: {empresa} {cargo} {candidato} {area} {cidade} {apresentacao}")
        vars_lbl.setObjectName("Muted")
        vars_lbl.setWordWrap(True)
        form.addRow("", vars_lbl)
        lv.addWidget(box)

        self.prepare_btn = QPushButton("PREPARAR CANDIDATURAS EM LOTE")
        self.prepare_btn.setObjectName("Primary")
        self.prepare_btn.clicked.connect(self.prepare)
        lv.addWidget(self.prepare_btn)
        lv.addStretch()
        splitter.addWidget(left)

        # ---- Seleção de contatos + fila ----
        right = QWidget()
        rv = QVBoxLayout(right)
        self.tabs = QTabWidget()

        # Tab 1: contatos para selecionar
        tab1 = QWidget()
        t1 = QVBoxLayout(tab1)
        sel_bar = QHBoxLayout()
        self.only_candidates = QCheckBox("Somente contatos adequados")
        self.only_candidates.setChecked(True)
        self.only_candidates.stateChanged.connect(self.load_contacts)
        sel_bar.addWidget(self.only_candidates)
        btn_all = QPushButton("Marcar todos")
        btn_all.clicked.connect(lambda: self._check_all(True))
        btn_none = QPushButton("Desmarcar")
        btn_none.clicked.connect(lambda: self._check_all(False))
        sel_bar.addWidget(btn_all)
        sel_bar.addWidget(btn_none)
        sel_bar.addStretch()
        self.sel_lbl = QLabel("")
        self.sel_lbl.setObjectName("Muted")
        sel_bar.addWidget(self.sel_lbl)
        t1.addLayout(sel_bar)
        self.contacts_table = make_table([
            ("sel", "✓"), ("email", "E-mail"), ("company", "Empresa"),
            ("status", "Status"),
        ])
        self.contacts_table.itemChanged.connect(self._update_sel_count)
        t1.addWidget(self.contacts_table)
        self.tabs.addTab(tab1, "Selecionar contatos")

        # Tab 2: fila/revisão
        tab2 = QWidget()
        t2 = QVBoxLayout(tab2)
        pan = QHBoxLayout()
        self.filter_status = QComboBox()
        self.filter_status.addItems(["Preparada", "Na fila", "Enviada", "Falha no envio", "Todas"])
        self.filter_status.currentIndexChanged.connect(self.load_applications)
        pan.addWidget(self.filter_status)
        pan.addStretch()
        t2.addLayout(pan)
        self.apps_table = make_table([
            ("company", "Empresa"), ("email", "Para"), ("subject", "Assunto"),
            ("score", "Score"), ("status", "Status"), ("sent", "Enviado em"),
        ], stretch_col=2)
        self.apps_table.itemSelectionChanged.connect(self._show_app)
        t2.addWidget(self.apps_table)

        edit_box = QGroupBox("Revisão da mensagem selecionada")
        ef = QFormLayout(edit_box)
        self.edit_subject = QLineEdit()
        self.edit_body = QPlainTextEdit()
        self.edit_body.setMinimumHeight(140)
        ef.addRow("Assunto", self.edit_subject)
        ef.addRow("Corpo", self.edit_body)
        save_btn = QPushButton("Salvar alterações desta mensagem")
        save_btn.clicked.connect(self.save_message_edit)
        ef.addRow("", save_btn)
        t2.addWidget(edit_box)
        self.tabs.addTab(tab2, "Fila e revisão")

        # Tab 3: envio
        tab3 = QWidget()
        t3 = QVBoxLayout(tab3)
        prov_box = QGroupBox("Envio (SMTP autenticado)")
        pf = QFormLayout(prov_box)
        self.preset = QComboBox()
        self.preset.addItems(list(PRESETS.keys()))
        self.preset.currentTextChanged.connect(self._apply_preset)
        self.host = QLineEdit(settings_repo.get("smtp_host", "smtp.gmail.com"))
        self.port = QLineEdit(settings_repo.get("smtp_port", "587"))
        self.user = QLineEdit(settings_repo.get("smtp_user", ""))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Senha de app (nunca é salva em texto puro)"
                                        if not get_secret("smtp_password")
                                        else "Senha já armazenada")
        self.delay = QDoubleSpinBox()
        self.delay.setRange(1, 600)
        self.delay.setValue(8)
        self.delay.setSuffix(" s")
        pf.addRow("Provedor", self.preset)
        pf.addRow("Servidor SMTP", self.host)
        pf.addRow("Porta", self.port)
        pf.addRow("Usuário", self.user)
        pf.addRow("Senha de app", self.password)
        pf.addRow("Intervalo entre envios", self.delay)
        t3.addWidget(prov_box)

        btns = QHBoxLayout()
        verify = QPushButton("Testar autenticação")
        verify.clicked.connect(self.verify_smtp)
        self.send_btn = QPushButton("Enviar aprovadas")
        self.send_btn.setObjectName("Success")
        self.send_btn.clicked.connect(self.send)
        self.pause_btn = QPushButton("Pausar")
        self.pause_btn.setObjectName("Warning")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("Danger")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel)
        btns.addWidget(verify)
        btns.addWidget(self.send_btn)
        btns.addWidget(self.pause_btn)
        btns.addWidget(self.cancel_btn)
        btns.addStretch()
        t3.addLayout(btns)
        t3.addStretch()
        self.tabs.addTab(tab3, "Envio")

        rv.addWidget(self.tabs)
        splitter.addWidget(right)
        splitter.setSizes([420, 900])
        self.root.addWidget(splitter)

        self._apply_preset(self.preset.currentText())
        self.load_resumes()
        self.load_contacts()
        self.load_applications()
        self._update_sel_count()

    # ---------- helpers ----------
    def load_resumes(self) -> None:
        self.resume.clear()
        active_idx = 0
        for i, r in enumerate(resume_repo.list()):
            self.resume.addItem(r["name"], r["id"])
            if r["is_active"]:
                active_idx = i
        if self.resume.count():
            self.resume.setCurrentIndex(active_idx)
        self._apply_language_template()

    def _apply_language_template(self) -> None:
        lang = "en" if self.language.currentText().startswith("en") else "pt"
        subj, body = default_templates(lang)
        if not self.subject.text():
            self.subject.setText(subj)
        if not self.body.toPlainText():
            self.body.setPlainText(body)

    def _apply_preset(self, name: str) -> None:
        preset = PRESETS.get(name)
        if preset and preset["host"]:
            self.host.setText(preset["host"])
            self.port.setText(str(preset["port"]))

    def load_contacts(self) -> None:
        self.contacts_table.blockSignals(True)
        self.contacts_table.setRowCount(0)
        rows = contact_repo.list(only_candidates=self.only_candidates.isChecked(),
                                 limit=3000)
        for c in rows:
            if not c["email"]:
                continue
            r = self.contacts_table.rowCount()
            self.contacts_table.insertRow(r)
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            check.setCheckState(Qt.Unchecked)
            check.setData(Qt.UserRole, c["id"])
            self.contacts_table.setItem(r, 0, check)
            self.contacts_table.setItem(r, 1, QTableWidgetItem(c["email"] or ""))
            self.contacts_table.setItem(r, 2, QTableWidgetItem(c["company_name"] or "—"))
            self.contacts_table.setItem(r, 3, status_item(c["status"] or ""))
        self.contacts_table.blockSignals(False)
        self._update_sel_count()

    def _check_all(self, state: bool) -> None:
        self.contacts_table.blockSignals(True)
        for r in range(self.contacts_table.rowCount()):
            self.contacts_table.item(r, 0).setCheckState(
                Qt.Checked if state else Qt.Unchecked)
        self.contacts_table.blockSignals(False)
        self._update_sel_count()

    def _selected_contact_ids(self) -> list[int]:
        ids = []
        for r in range(self.contacts_table.rowCount()):
            item = self.contacts_table.item(r, 0)
            if item and item.checkState() == Qt.Checked:
                ids.append(item.data(Qt.UserRole))
        return ids

    def _update_sel_count(self, *_) -> None:
        n = len(self._selected_contact_ids())
        self.sel_lbl.setText(f"{n} selecionado(s)")

    # ---------- prepare ----------
    def prepare(self) -> None:
        ids = self._selected_contact_ids()
        if not ids:
            self.toast("Selecione ao menos um contato.", "warning")
            return
        if not self.resume.count():
            self.toast("Importe um currículo primeiro (tela Meu currículo).", "warning")
            return
        lang = "en" if self.language.currentText().startswith("en") else "pt"
        cid = campaign_repo.create(
            name=self.name.text().strip() or "Campanha",
            resume_id=self.resume.currentData(),
            subject_tpl=self.subject.text().strip(),
            body_tpl=self.body.toPlainText(),
            language=lang,
        )
        campaign_repo.update(cid, from_email=self.from_email.text().strip())
        self.campaign_id = cid
        self.prepare_btn.setEnabled(False)
        self.toast("Preparando mensagens…", "info")
        self.worker = Worker(campaign_engine.prepare, cid, ids,
                             use_ai=self.use_ai.isChecked(), with_progress=True)
        self.worker.progress.connect(lambda c, t, m: None)
        self.worker.finished_ok.connect(self._prepared)
        self.worker.failed.connect(lambda e: self._prepare_fail(e))
        self.worker.start()

    def _prepare_fail(self, err: str) -> None:
        self.prepare_btn.setEnabled(True)
        self.toast(f"Falha ao preparar: {err.splitlines()[0]}", "error")

    def _prepared(self, report) -> None:
        self.prepare_btn.setEnabled(True)
        msg = f"{report.prepared} candidaturas preparadas, {report.skipped} ignoradas."
        if report.ai_unavailable:
            msg += " IA indisponível — usados os modelos."
        if report.errors:
            msg += " " + " ".join(report.errors[:2])
        self.toast(msg, "warning" if report.errors else "success")
        self.tabs.setCurrentIndex(1)
        self.load_applications()

    # ---------- review ----------
    def load_applications(self) -> None:
        status = self.filter_status.currentText()
        status = "" if status == "Todas" else status
        self.apps_table.setRowCount(0)
        for a in application_repo.list(campaign_id=self.campaign_id, status=status):
            r = self.apps_table.rowCount()
            self.apps_table.insertRow(r)
            self.apps_table.setItem(r, 0, QTableWidgetItem(a["company_name"] or "—"))
            self.apps_table.setItem(r, 1, QTableWidgetItem(a["to_email"] or ""))
            self.apps_table.setItem(r, 2, QTableWidgetItem(a["subject"] or ""))
            score = a["match_score"]
            self.apps_table.setItem(r, 3, QTableWidgetItem("" if score is None else f"{score:.0f}"))
            self.apps_table.setItem(r, 4, status_item(a["status"] or ""))
            self.apps_table.setItem(r, 5, QTableWidgetItem((a["sent_at"] or "")[:16]))
            self.apps_table.item(r, 0).setData(Qt.UserRole, a["id"])

    def _show_app(self) -> None:
        items = self.apps_table.selectedItems()
        if not items:
            return
        aid = self.apps_table.item(items[0].row(), 0).data(Qt.UserRole)
        a = application_repo.get(aid)
        if a:
            self.edit_subject.setText(a["subject"] or "")
            self.edit_body.setPlainText(a["body"] or "")
            self._current_app_id = aid

    def save_message_edit(self) -> None:
        aid = getattr(self, "_current_app_id", None)
        if not aid:
            self.toast("Selecione uma mensagem.", "warning")
            return
        application_repo.update(aid, subject=self.edit_subject.text(),
                                body=self.edit_body.toPlainText())
        self.toast("Mensagem atualizada.", "success")
        self.load_applications()

    # ---------- send ----------
    def _build_provider(self) -> SmtpProvider | None:
        user = self.user.text().strip()
        password = self.password.text() or get_secret("smtp_password") or ""
        if not user:
            self.toast("Informe o usuário SMTP.", "error")
            return None
        if not password:
            self.toast("Informe a senha de app do provedor.", "error")
            return None
        security = "starttls"
        port = int(self.port.text() or "587")
        if port == 465:
            security = "ssl"
        return SmtpProvider(
            host=self.host.text().strip(), port=port, username=user,
            password=password, from_email=settings_repo.get("smtp_from", "") or user,
            security=security,
        )

    def verify_smtp(self) -> None:
        provider = self._build_provider()
        if not provider:
            return
        if self.password.text():
            from ...security.credentials import set_secret
            set_secret("smtp_password", self.password.text())
            settings_repo.set("smtp_host", self.host.text().strip())
            settings_repo.set("smtp_port", self.port.text().strip())
            settings_repo.set("smtp_user", self.user.text().strip())
            settings_repo.set("smtp_from", self.from_email.text().strip() or self.user.text().strip())
        self.toast("Testando autenticação…", "info")
        self.worker = Worker(provider.verify_login)
        self.worker.finished_ok.connect(lambda r: self.toast(r[1], "success" if r[0] else "error"))
        self.worker.failed.connect(lambda e: self.toast(e.splitlines()[0], "error"))
        self.worker.start()

    def send(self) -> None:
        if not self.campaign_id:
            self.toast("Prepare uma campanha antes de enviar.", "warning")
            return
        provider = self._build_provider()
        if not provider:
            return
        pending = [a for a in application_repo.list(campaign_id=self.campaign_id)
                   if a["status"] == "Preparada"]
        if not pending:
            self.toast("Nenhuma candidatura preparada para enviar.", "warning")
            return
        reply = QMessageBox.question(
            self, "Confirmar envio",
            f"Enviar {len(pending)} candidaturas?\n\n"
            "As mensagens serão enviadas pelo provedor configurado. "
            "Você pode pausar ou cancelar a qualquer momento.",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        if self.password.text():
            from ...security.credentials import set_secret
            set_secret("smtp_password", self.password.text())
            settings_repo.set("smtp_host", self.host.text().strip())
            settings_repo.set("smtp_port", self.port.text().strip())
            settings_repo.set("smtp_user", self.user.text().strip())

        self._stop_event.clear()
        self._pause_event.clear()
        self.send_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.toast("Enviando… respeitando os limites do provedor.", "info")
        self.worker = Worker(campaign_engine.send_queue, self.campaign_id, provider,
                             delay_seconds=self.delay.value(),
                             stop_event=self._stop_event, pause_event=self._pause_event,
                             with_progress=True)
        self.worker.progress.connect(lambda c, t, m: None)
        self.worker.finished_ok.connect(self._sent)
        self.worker.failed.connect(self._send_fail)
        self.worker.start()

    def _send_fail(self, err: str) -> None:
        self._reset_send_buttons()
        self.toast(f"Falha no envio: {err.splitlines()[0]}", "error")

    def _sent(self, report) -> None:
        self._reset_send_buttons()
        msg = f"Enviadas: {report.sent} • Falhas: {report.failed} • Ignoradas: {report.skipped}"
        if report.aborted:
            msg += " (cancelada pelo usuário)"
        self.toast(msg, "success" if report.sent and not report.failed else "warning")
        self.load_applications()

    def _reset_send_buttons(self) -> None:
        self.send_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("Pausar")
        self.cancel_btn.setEnabled(False)

    def toggle_pause(self) -> None:
        if self._pause_event.is_set():
            self._pause_event.clear()
            self.pause_btn.setText("Pausar")
            self.toast("Envio retomado.", "info")
        else:
            self._pause_event.set()
            self.pause_btn.setText("Retomar")
            self.toast("Envio pausado.", "info")

    def cancel(self) -> None:
        self._stop_event.set()
        self._pause_event.clear()
        self.toast("Cancelando exportação da fila…", "warning")

    def on_show(self) -> None:
        self.load_resumes()
        self.load_contacts()
        self.load_applications()
