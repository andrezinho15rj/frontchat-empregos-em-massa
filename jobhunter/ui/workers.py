"""Worker genérico para executar tarefas em thread separada (UI não trava)."""
from __future__ import annotations

import traceback
from typing import Callable

from PySide6.QtCore import QThread, Signal

from ..logging_setup import get_logger

log = get_logger("ui.worker")


class Worker(QThread):
    """Executa `fn(*args, **kwargs)` em background.

    A função pode receber um parâmetro opcional `progress` (callable) se
    `with_progress=True`.
    """

    finished_ok = Signal(object)
    failed = Signal(str)
    progress = Signal(int, int, str)

    def __init__(self, fn: Callable, *args, with_progress: bool = False, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.with_progress = with_progress
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def is_stopped(self) -> bool:
        return self._stop

    def run(self) -> None:
        try:
            if self.with_progress:
                self.kwargs["progress"] = self._progress_cb
            result = self.fn(*self.args, **self.kwargs)
            self.finished_ok.emit(result)
        except Exception as exc:  # pragma: no cover
            log.exception("Erro em worker")
            self.failed.emit(f"{exc}\n\n{traceback.format_exc()}")

    def _progress_cb(self, current: int, total: int, message: str = "") -> None:
        self.progress.emit(int(current), int(total), str(message))
