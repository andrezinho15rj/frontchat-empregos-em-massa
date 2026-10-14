@echo off
REM ============================================================
REM  Frontchat Empregos em Massa - Script de compilacao do EXE
REM  Requer: Python 3.10+ e PyInstaller instalado no venv.
REM ============================================================
setlocal
cd /d "%~dp0"

echo [1/5] Verificando ambiente virtual...
if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv .venv || goto :erro
)

echo [2/5] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller || goto :erro

echo [3/5] Gerando icone...
".venv\Scripts\python.exe" scripts\make_icon.py

echo [4/5] Compilando com PyInstaller...
".venv\Scripts\python.exe" -m PyInstaller jobhunter.spec --noconfirm --clean || goto :erro

echo [5/5] Concluido!
echo.
echo Executavel gerado em: dist\FrontchatEmpregosEmMassa.exe
echo Para criar o instalador, abra installer\FrontchatEmpregosEmMassa.iss no Inno Setup.
goto :fim

:erro
echo.
echo *** FALHA NA COMPILACAO ***
exit /b 1

:fim
endlocal
exit /b 0
