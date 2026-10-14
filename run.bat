@echo off
REM Executa o Frontchat Empregos em Massa a partir do codigo-fonte (desenvolvimento).
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado. Rode build.bat primeiro.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py
endlocal
