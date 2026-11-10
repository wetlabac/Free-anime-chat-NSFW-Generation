@echo off
chcp 65001 >nul
title Stop AI Stack

echo ============================================
echo          STOPPING AI STACK
echo ============================================
echo.

echo [1/3] Ollama...
taskkill /F /IM ollama.exe /T
taskkill /F /IM "ollama app.exe" /T
echo.

echo [2/3] SillyTavern, port 8000...
call :kill_port 8000
echo.
echo Закрываю процесс SillyTavern...
powershell.exe -NoProfile -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*E:\AI\SillyTavern*' -or $_.ExecutablePath -like '*SillyTavern*' }; if ($procs) { $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force } } else { Write-Host 'SillyTavern process not found' }"

echo [3/3] ComfyUI, port 8188...
call :kill_port 8188
echo.

echo Закрываю окна запуска...
taskkill /F /FI "WINDOWTITLE eq ComfyUI*" /IM cmd.exe /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq SillyTavern*" /IM cmd.exe /T >nul 2>&1
echo ============================================
echo          FINISHED. BOT LEFT RUNNING.
echo ============================================
timeout /t 3 >nul
exit /b 0

:kill_port
set "PORT_PID_FOUND="
for /f "delims=" %%P in ('powershell.exe -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort %~1 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique"') do (
    set "PORT_PID_FOUND=1"
    echo Завершаю PID %%P на порту %~1...
    taskkill /PID %%P /F /T
)
if not defined PORT_PID_FOUND echo Не найден слушающий процесс на порту %~1.
exit /b 0