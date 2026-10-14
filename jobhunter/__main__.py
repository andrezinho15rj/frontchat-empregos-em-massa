"""Ponto de entrada do Frontchat Empregos em Massa.

Uso:  python -m jobhunter   ou   python main.py
"""
from __future__ import annotations

import sys
import traceback


def _install_excepthook(app):
    def hook(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        from .logging_setup import get_logger
        get_logger("main").error("Exceção não tratada:\n%s", text)
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None, "Erro inesperado",
                f"Ocorreu um erro inesperado:\n\n{exc_value}\n\n"
                "Detalhes foram registrados no log (pasta de dados/logs).")
        except Exception:
            print(text, file=sys.stderr)
    sys.excepthook = hook


def run() -> int:
    from .logging_setup import setup_logging, get_logger
    setup_logging()
    log = get_logger("main")
    log.info("Iniciando Frontchat Empregos em Massa")

    # Banco de dados (criado automaticamente no primeiro uso)
    from .db.database import database
    database.initialize()

    from PySide6.QtWidgets import QApplication
    from .ui.main_window import MainWindow
    from . import app_paths

    app = QApplication(sys.argv)
    app.setApplicationName("Frontchat Empregos em Massa")
    app.setOrganizationName("Frontchat")
    _install_excepthook(app)

    icon_path = app_paths.resource_path("assets/icon.ico")
    if icon_path.exists():
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    log.info("Interface pronta.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
