@echo off
setlocal

set "AI_DIR=E:\AI"
set "COMFY_DIR=E:\AI\ComfyUI"
set "COMFY_BAT=E:\AI\ComfyUI\run_nvidia_gpu.bat"
set "ST_DIR=E:\AI\SillyTavern"
set "ST_BAT=E:\AI\SillyTavern\Start.bat"

echo Проверяю файлы...

if not exist "%COMFY_BAT%" (
    echo ОШИБКА: не найден "%COMFY_BAT%"
    pause
    exit /b 1
)

if not exist "%ST_BAT%" (
    echo ОШИБКА: не найден "%ST_BAT%"
    pause
    exit /b 1
)

echo Проверяю Ollama...
call :check_port 11434

if errorlevel 1 (
    if not exist "E:\AI\Ollama\ollama.exe" (
        echo ОШИБКА: не найден E:\AI\Ollama\ollama.exe
    ) else (
        echo Запускаю Ollama...
        start "Ollama" /min "E:\AI\Ollama\ollama.exe" serve
        timeout /t 5 /nobreak >nul

        call :check_port 11434
        if errorlevel 1 (
            echo Ollama запущена, но порт 11434 пока не отвечает.
        ) else (
            echo Ollama работает.
        )
    )
) else (
    echo Ollama уже запущена.
)

echo Проверяю ComfyUI...
call :check_port 8188

if errorlevel 1 (
    echo Запускаю ComfyUI...
    start "ComfyUI" /D "%COMFY_DIR%" /min cmd.exe /c run_nvidia_gpu.bat
) else (
    echo ComfyUI уже запущен.
)

echo Проверяю SillyTavern...
call :check_port 8000

if errorlevel 1 (
    echo Запускаю SillyTavern...
    start "SillyTavern" /min cmd.exe /c call "%ST_BAT%"
) else (
    echo SillyTavern уже запущен.
)

echo.
echo Команды запуска отправлены.
echo Для телефона используй: http://IP-АДРЕС-КОМПЬЮТЕРА:8000
echo Узнать IP компьютера можно командой: ipconfig
exit /b 0

:check_port
powershell -NoProfile -Command "try { $c=New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1',%~1); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
exit /b %errorlevel%