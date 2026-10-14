"""Gera capturas das telas para conferência visual (modo offscreen)."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402
from jobhunter.db.database import database  # noqa: E402
from jobhunter.ui.main_window import MainWindow  # noqa: E402
from jobhunter.db.repositories import settings_repo  # noqa: E402


def main():
    database.initialize()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1360, 860)
    w.show()
    app.processEvents()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shots")
    os.makedirs(out, exist_ok=True)
    for i in range(10):
        w.goto(i)
        app.processEvents()
        w.repaint()
        app.processEvents()
        pix = w.grab()
        pix.save(os.path.join(out, f"tela_{i:02d}.png"))
    print("Capturas salvas em", os.path.abspath(out))


if __name__ == "__main__":
    main()
