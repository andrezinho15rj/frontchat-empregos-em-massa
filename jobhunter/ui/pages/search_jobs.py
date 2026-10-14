"""Página 2 — Buscar vagas (pesquisa real em fontes autorizadas)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QSpinBox, QVBoxLayout,
)

from ...constants import AREA_OPTIONS, PUBLICATION_PERIODS
from ...search import SearchFilters, search_manager
from ..widgets import add_row, make_table
from ..workers import Worker
from .base import PageBase


class SearchJobsPage(PageBase):
    title = "Buscar vagas"
    subtitle = "Pesquise oportunidades em fontes autorizadas (APIs públicas e oficiais)."

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)
        self.worker: Worker | None = None

        filter_box = QGroupBox("Filtros de pesquisa")
        form = QGridLayout(filter_box)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.query = QLineEdit()
        self.query.setPlaceholderText("Cargo, palavra-chave (ex.: Analista Administrativo)")
        self.country = QLineEdit("Brasil")
        self.state = QLineEdit()
        self.state.setPlaceholderText("Estado (ex.: SP)")
        self.city = QLineEdit()
        self.city.setPlaceholderText("Cidade")
        self.neighborhood = QLineEdit()
        self.neighborhood.setPlaceholderText("Bairro")
        self.area = QComboBox()
        self.area.addItems([""] + AREA_OPTIONS)
        self.contract = QComboBox()
        self.contract.addItems(["", "CLT", "Estágio", "Jovem Aprendiz",
                                "Temporário", "Freelancer", "PJ", "Remoto"])
        self.work_mode = QComboBox()
        self.work_mode.addItems(["", "Presencial", "Híbrido", "Remoto"])
        self.period = QComboBox()
        self.period.addItems(list(PUBLICATION_PERIODS.keys()))
        self.period.setCurrentText("Últimos 7 dias")
        self.limit = QSpinBox()
        self.limit.setRange(10, 300)
        self.limit.setValue(60)

        fields = [
            ("Cargo / Palavra-chave", self.query, 0, 0, 1, 3),
            ("País", self.country, 1, 0), ("Estado", self.state, 1, 1),
            ("Cidade", self.city, 1, 2), ("Bairro", self.neighborhood, 1, 3),
            ("Área", self.area, 2, 0), ("Tipo de emprego", self.contract, 2, 1),
            ("Modalidade", self.work_mode, 2, 2), ("Publicação", self.period, 2, 3),
            ("Máx. por fonte", self.limit, 3, 0),
        ]
        for spec in fields:
            label, widget = spec[0], spec[1]
            r, c = spec[2], spec[3]
            rs = spec[4] if len(spec) > 4 else 1
            cs = spec[5] if len(spec) > 5 else 1
            box = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setObjectName("Muted")
            box.addWidget(lbl)
            box.addWidget(widget)
            form.addLayout(box, r, c, rs, cs)

        self.root.addWidget(filter_box)

        actions = QHBoxLayout()
        self.search_btn = QPushButton("Pesquisar vagas")
        self.search_btn.setObjectName("Primary")
        self.search_btn.clicked.connect(self.run_search)
        self.contacts_btn = QPushButton("Buscar contatos das vagas")
        self.contacts_btn.clicked.connect(self.discover_contacts)
        self.contacts_btn.setEnabled(False)
        actions.addWidget(self.search_btn)
        actions.addWidget(self.contacts_btn)
        actions.addStretch()
        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("Muted")
        actions.addWidget(self.status_lbl)
        self.root.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.root.addWidget(self.progress)

        results_lbl = QLabel("Resultados")
        results_lbl.setObjectName("SectionTitle")
        self.root.addWidget(results_lbl)
        self.empty_lbl = QLabel("")
        self.empty_lbl.setObjectName("Muted")
        self.empty_lbl.setWordWrap(True)
        self.empty_lbl.setVisible(False)
        self.root.addWidget(self.empty_lbl)
        self.table = make_table([
            ("title", "Cargo"), ("company", "Empresa"), ("location", "Local"),
            ("mode", "Modalidade"), ("source", "Fonte"), ("published", "Publicado"),
            ("url", "URL"),
        ], stretch_col=6)
        self.root.addWidget(self.table)

    def _build_filters(self) -> SearchFilters:
        days = PUBLICATION_PERIODS.get(self.period.currentText(), 7)
        ct = self.contract.currentText()
        wm = self.work_mode.currentText()
        if ct == "Remoto":
            wm = "Remoto"
            ct = ""
        return SearchFilters(
            query=self.query.text().strip(),
            country=self.country.text().strip(),
            state=self.state.text().strip(),
            city=self.city.text().strip(),
            neighborhood=self.neighborhood.text().strip(),
            work_mode=wm, contract_type=ct,
            area=self.area.currentText(),
            days=days,
        )

    def run_search(self) -> None:
        filters = self._build_filters()
        self.search_btn.setEnabled(False)
        self.contacts_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.status_lbl.setText("Pesquisando...")
        self.worker = Worker(self._do_search, filters, with_progress=True)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.failed.connect(self._on_fail)
        self.worker.start()

    def _do_search(self, filters: SearchFilters, progress=None):
        def cb(msg):
            if progress:
                progress(0, 0, msg)
        return search_manager.search(filters, max_per_source=self.limit.value(),
                                     on_progress=cb)

    def _on_progress(self, cur, total, msg) -> None:
        if msg:
            self.status_lbl.setText(msg)

    def _on_done(self, report) -> None:
        self.progress.setVisible(False)
        self.search_btn.setEnabled(True)
        self.contacts_btn.setEnabled(True)
        self.status_lbl.setText(
            f"Encontradas {report.total_found} • salvas {report.total_saved}")
        msg = f"Busca concluída: {report.total_saved} vagas salvas."
        if report.errors:
            detalhes = "; ".join(f"{k}: {v}" for k, v in report.errors.items())
            self.toast(f"{msg} Avisos — {detalhes}", "warning")
        else:
            self.toast(msg, "success")
        self.load_table()

    def _on_fail(self, err: str) -> None:
        self.progress.setVisible(False)
        self.search_btn.setEnabled(True)
        self.toast(f"Erro na busca: {err.splitlines()[0]}", "error")

    def load_table(self) -> None:
        from ...db.repositories import job_repo
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for job in job_repo.list(limit=1000):
            add_row(self.table, [
                job["title"], job["company_name"] or "—",
                job["location"] or job["city"] or "—",
                job["work_mode"] or "—", job["source"],
                (job["published_at"] or "")[:10], job["url"],
            ], user_data=job["id"])
        self.table.setSortingEnabled(True)
        total = self.table.rowCount()
        if total == 0:
            self.empty_lbl.setText(
                "Nenhuma vaga encontrada. Verifique a conexão com a internet, "
                "reduza a busca (limpe o campo Cargo) e clique em “Pesquisar vagas”.")
            self.empty_lbl.setVisible(True)
        else:
            self.empty_lbl.setVisible(False)

    def discover_contacts(self) -> None:
        from ...db.repositories import job_repo
        jobs = [j for j in job_repo.list(limit=1000) if j["company_id"]]
        if not jobs:
            self.toast("Nenhuma vaga com empresa identificada. Pesquise vagas primeiro.", "warning")
            return
        self.contacts_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(jobs))
        self.status_lbl.setText("Buscando contatos públicos...")
        self.worker = Worker(self._do_discover, [j["id"] for j in jobs], with_progress=True)
        self.worker.progress.connect(lambda c, t, m: self.progress.setValue(c))
        self.worker.finished_ok.connect(self._on_discover_done)
        self.worker.failed.connect(self._on_fail)
        self.worker.start()

    def _do_discover(self, job_ids, progress=None):
        from ...contacts import contact_discovery
        from ...contacts.contact_finder import ContactDiscoveryReport
        agg = ContactDiscoveryReport()
        for i, jid in enumerate(job_ids):
            if progress:
                progress(i + 1, len(job_ids), "")
            try:
                rep = contact_discovery.find_for_job(jid)
                agg.companies_processed += rep.companies_processed
                agg.emails_found += rep.emails_found
                agg.emails_saved += rep.emails_saved
                agg.forms_found += rep.forms_found
                agg.phones_saved += rep.phones_saved
                agg.errors.extend(rep.errors)
            except Exception as exc:
                agg.errors.append(str(exc))
        return agg

    def _on_discover_done(self, report) -> None:
        self.progress.setVisible(False)
        self.contacts_btn.setEnabled(True)
        self.search_btn.setEnabled(True)
        self.status_lbl.setText(f"Contatos: {report.emails_saved} e-mails, "
                                f"{report.phones_saved} telefones, "
                                f"{report.forms_found} formulários.")
        self.toast(f"Descoberta concluída: {report.emails_saved} e-mails, "
                   f"{report.phones_saved} telefones, "
                   f"{report.forms_found} formulários.", "success")

    def on_show(self) -> None:
        self.load_table()
