@echo off
chcp 65001 >nul
title MRFA Unloader
echo [MRFA] Usuwanie agenta z komputera...

schtasks /delete /tn "MRFA_Agent" /f
taskkill /f /im python.exe /fi "windowtitle eq agent.py"
del %USERPROFILE%\agent.py
del %USERPROFILE%\.mrfa_agent_config.json

echo [MRFA] Agent usunięty.
pause
