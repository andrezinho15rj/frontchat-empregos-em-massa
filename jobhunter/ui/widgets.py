"""Widgets reutilizáveis da interface."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget, QAbstractItemView, QHeaderView,
)

from . import theme


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")


class MetricCard(QFrame):
    def __init__(self, label: str, value: str = "0", accent: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 16, 0)
        outer.setSpacing(14)

        stripe = QFrame()
        stripe.setFixedWidth(5)
        color = theme.ACCENT_2 if accent else theme.ACCENT
        stripe.setStyleSheet(f"background: {color}; border-top-left-radius: 16px; "
                             f"border-bottom-left-radius: 16px;")
        outer.addWidget(stripe)

        col = QVBoxLayout()
        col.setContentsMargins(2, 15, 0, 15)
        col.setSpacing(3)
        self.value_lbl = QLabel(str(value))
        self.value_lbl.setObjectName("MetricValue")
        self.value_lbl.setStyleSheet(f"color: {color};")
        self.label_lbl = QLabel(label)
        self.label_lbl.setObjectName("MetricLabel")
        col.addWidget(self.value_lbl)
        col.addWidget(self.label_lbl)
        outer.addLayout(col)
        outer.addStretch()

    def set_value(self, value) -> None:
        self.value_lbl.setText(str(value))


def make_table(columns: list[tuple[str, str]], stretch_col: int = -1) -> QTableWidget:
    """Cria uma QTableWidget configurada. columns = [(key, título), ...]"""
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels([title for _, title in columns])
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.ExtendedSelection)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.setSortingEnabled(True)
    table.horizontalHeader().setStretchLastSection(True)
    if stretch_col >= 0:
        table.horizontalHeader().setSectionResizeMode(
            stretch_col, QHeaderView.Stretch)
    return table


def add_row(table: QTableWidget, values: list[str], user_data=None,
            tooltip: str = "") -> None:
    row = table.rowCount()
    table.insertRow(row)
    for col, val in enumerate(values):
        item = QTableWidgetItem(str(val) if val is not None else "")
        if col == 0 and user_data is not None:
            item.setData(Qt.UserRole, user_data)
        if tooltip:
            item.setToolTip(tooltip)
        table.setItem(row, col, item)


STATUS_COLORS = {
    "Encontrado e origem confirmada": "#2EBD85",
    "Domínio válido, entrega não confirmada": "#E2A93B",
    "E-mail inválido": "#E5534B",
    "E-mail duplicado": "#95A2B8",
    "Contato inadequado para candidatura": "#C98A17",
    "Formulário de candidatura disponível": "#2F6BFF",
    "Telefone encontrado": "#7C5CFF",
    "Não verificado": "#95A2B8",
    "Enviada": "#2EBD85",
    "Falha no envio": "#E5534B",
    "Preparada": "#2F6BFF",
    "Na fila": "#E2A93B",
    "Cancelada": "#95A2B8",
    "Resposta recebida": "#2EBD85",
    "Entrevista": "#2EBD85",
}


def status_item(status: str) -> QTableWidgetItem:
    item = QTableWidgetItem(status or "")
    color = STATUS_COLORS.get(status, "#95A2B8")
    item.setForeground(QColor(color))
    return item


class Toast(QLabel):
    """Notificação não invasiva temporária."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, level: str = "info", msec: int = 4000) -> None:
        colors = {"info": theme.ACCENT, "success": "#2EBD85",
                  "warning": "#E2A93B", "error": "#E5534B"}
        color = colors.get(level, theme.ACCENT)
        self.setStyleSheet(
            f"background: {color}; color: white; border-radius: 8px; "
            f"padding: 10px 16px; font-weight: 600;")
        self.setText(text)
        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()
        self._timer.start(msec)

    def _reposition(self) -> None:
        par = self.parentWidget()
        if par:
            w = min(max(self.width() + 40, 320), par.width() - 40)
            self.setFixedWidth(w)
            self.move((par.width() - w) // 2, par.height() - self.height() - 24)
