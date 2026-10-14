@echo off
REM Executa os testes automatizados.
setlocal
cd /d "%~dp0"
set QT_QPA_PLATFORM=offscreen
".venv\Scripts\python.exe" -m unittest discover -s tests -t . -v
endlocal
