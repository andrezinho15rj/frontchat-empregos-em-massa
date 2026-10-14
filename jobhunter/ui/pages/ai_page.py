"""Página 7 — Inteligência artificial (configuração e testes)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ...ai import test_connection
from ...db.repositories import settings_repo
from ...security.credentials import get_secret, set_secret
from ..workers import Worker
from .base import PageBase


class AIPage(PageBase):
    title = "Inteligência artificial"
    subtitle = ("Módulo opcional. A IA nunca inventa experiências — apenas usa o que "
                "está no seu currículo.")

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)

        box = QGroupBox("Configuração da API (compatível com OpenAI)")
        form = QFormLayout(box)
        self.base_url = QLineEdit(settings_repo.get("ai_base_url", "https://api.openai.com/v1"))
        self.model = QLineEdit(settings_repo.get("ai_model", "gpt-4o-mini"))
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_key.setPlaceholderText("Cole a chave (salva no Windows, nunca em texto puro)"
                                        if not get_secret("ai_api_key") else "Chave já armazenada")
        form.addRow("Base URL", self.base_url)
        form.addRow("Modelo", self.model)
        form.addRow("Chave de API", self.api_key)

        btn_row = QHBoxLayout()
        save = QPushButton("Salvar configuração")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        test = QPushButton("Testar conexão")
        test.clicked.connect(self.test)
        btn_row.addWidget(save)
        btn_row.addWidget(test)
        btn_row.addStretch()
        holder = QWidget()
        holder.setLayout(btn_row)
        form.addRow("", holder)

        hint = QLabel(
            "Compatível com OpenAI, Groq, OpenRouter e Ollama (openai-compat). "
            "Para Ollama local, deixe a chave em branco e use "
            "http://localhost:11434/v1.")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        form.addRow("", hint)
        self.root.addWidget(box)

        tools = QGroupBox("Teste rápido de compatibilidade")
        tform = QFormLayout(tools)
        self.job_title = QLineEdit()
        self.job_title.setPlaceholderText("Título da vaga (ou deixe em branco para usar a última vaga)")
        tform.addRow("Cargo", self.job_title)
        run = QPushButton("Analisar com IA")
        run.clicked.connect(self.analyze)
        tform.addRow("", run)
        self.root.addWidget(tools)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.root.addWidget(self.output)

    def save(self) -> None:
        settings_repo.set("ai_base_url", self.base_url.text().strip())
        settings_repo.set("ai_model", self.model.text().strip())
        if self.api_key.text().strip():
            set_secret("ai_api_key", self.api_key.text().strip())
            self.api_key.clear()
        self.toast("Configuração de IA salva.", "success")

    def test(self) -> None:
        self.toast("Testando conexão…", "info")
        self.worker = Worker(test_connection)
        self.worker.finished_ok.connect(self._test_done)
        self.worker.failed.connect(lambda e: self.toast(e.splitlines()[0], "error"))
        self.worker.start()

    def _test_done(self, result) -> None:
        ok, msg = result
        self.output.setPlainText(msg)
        self.toast(msg, "success" if ok else "error")

    def analyze(self) -> None:
        from ...ai.analyzer import AIAnalyzer
        from ...db.repositories import job_repo, resume_repo
        resume = resume_repo.active()
        if not resume:
            self.toast("Importe um currículo primeiro.", "warning")
            return
        title = self.job_title.text().strip()
        job = None
        if title:
            rows = job_repo.list(search=title, limit=1)
            job = rows[0] if rows else None
        if not job:
            rows = job_repo.list(limit=1)
            job = rows[0] if rows else None
        if not job:
            self.toast("Nenhuma vaga disponível. Pesquise vagas primeiro.", "warning")
            return
        analyzer = AIAnalyzer()
        if not analyzer.is_available():
            self.toast("IA não configurada.", "error")
            return
        self.toast("Analisando…", "info")
        self.worker = Worker(
            analyzer.match, job["title"], job["description"] or "", resume["content_text"] or "")
        self.worker.finished_ok.connect(self._analysis_done)
        self.worker.failed.connect(lambda e: self.toast(e.splitlines()[0], "error"))
        self.worker.start()

    def _analysis_done(self, result) -> None:
        lines = [f"Vaga analisada — compatibilidade: {result.get('score')}%",
                 f"Prioridade sugerida: {result.get('priority') or '—'}",
                 "", "Habilidades relevantes:",
                 ", ".join(result.get("skills") or []) or "—",
                 "", "Lacunas / não confirmado:",
                 ", ".join(result.get("gaps") or []) or "—",
                 "", "Justificativa:", result.get("reason") or "—"]
        self.output.setPlainText("\n".join(lines))
        self.toast("Análise concluída.", "success")
