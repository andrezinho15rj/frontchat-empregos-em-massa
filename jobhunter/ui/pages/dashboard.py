"""Página 1 — Dashboard com métricas reais do banco."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QVBoxLayout,
)

from ... import stats
from ..widgets import MetricCard, add_row, make_table, status_item
from .base import PageBase


class DashboardPage(PageBase):
    title = "Dashboard"
    subtitle = "Visão geral em tempo real das suas oportunidades e candidaturas."

    def __init__(self, app_window=None, parent=None):
        super().__init__(app_window, parent)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh)
        toolbar.addWidget(refresh)
        self.root.addLayout(toolbar)

        indicators = QLabel("Indicadores")
        indicators.setObjectName("SectionTitle")
        self.root.addWidget(indicators)

        grid = QGridLayout()
        grid.setSpacing(14)
        self.cards: dict[str, MetricCard] = {}
        specs = [
            ("empresas", "Empresas encontradas", False),
            ("vagas", "Vagas abertas identificadas", True),
            ("contatos", "Contatos de recrutamento", False),
            ("contatos_verificados", "Contatos verificados", True),
            ("candidaturas_preparadas", "Candidaturas preparadas", False),
            ("emails_enviados", "E-mails enviados", True),
            ("envios_falha", "Envios com falha", False),
            ("respostas", "Respostas recebidas", False),
            ("entrevistas", "Entrevistas registradas", False),
        ]
        for i, (key, label, accent) in enumerate(specs):
            card = MetricCard(label, "0", accent=accent)
            self.cards[key] = card
            grid.addWidget(card, i // 3, i % 3)
        self.root.addLayout(grid)

        activity = QLabel("Atividade recente")
        activity.setObjectName("SectionTitle")
        self.root.addWidget(activity)
        self.table = make_table([
            ("company", "Empresa"), ("to_email", "E-mail"), ("subject", "Assunto"),
            ("status", "Status"), ("when", "Quando"),
        ], stretch_col=2)
        self.root.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        metrics = stats.dashboard_metrics()
        for key, card in self.cards.items():
            card.set_value(metrics.get(key, 0))
        self.table.setRowCount(0)
        for row in stats.recent_activity(20):
            when = row["sent_at"] or row["updated_at"] or ""
            self.table.insertRow(self.table.rowCount())
            r = self.table.rowCount() - 1
            self.table.setItem(r, 0, _item(row["company"] or "—"))
            self.table.setItem(r, 1, _item(row["to_email"] or "—"))
            self.table.setItem(r, 2, _item(row["subject"] or "—"))
            self.table.setItem(r, 3, status_item(row["status"] or ""))
            self.table.setItem(r, 4, _item(when))

    def on_show(self) -> None:
        self.refresh()


def _item(text: str):
    from PySide6.QtWidgets import QTableWidgetItem
    return QTableWidgetItem(str(text) if text is not None else "")
