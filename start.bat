@echo off
setlocal EnableDelayedExpansion

:: Set up logging
set "LOGFILE=app_startup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "LOGFILE=%LOGFILE: =0%"

:: Debug mode flag (can be enabled with /debug parameter)
set "DEBUG_MODE=0"
if "%1"=="/debug" set "DEBUG_MODE=1"

echo [%date% %time%] Starting application... > "%LOGFILE%"

:: Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH! >> "%LOGFILE%"
    echo [ERROR] Python is not installed or not in PATH!
    exit /b 1
)

:: Check if manage.py exists
if not exist "manage.py" (
    echo [ERROR] manage.py not found in current directory! >> "%LOGFILE%"
    echo [ERROR] manage.py not found in current directory!
    exit /b 1
)

:: If debug mode is enabled, show more information
if %DEBUG_MODE%==1 (
    echo [DEBUG] Debug mode enabled >> "%LOGFILE%"
    echo [DEBUG] Debug mode enabled
    echo [DEBUG] Python version: >> "%LOGFILE%"
    python --version >> "%LOGFILE%" 2>&1
    echo [DEBUG] Current directory: >> "%LOGFILE%"
    cd >> "%LOGFILE%"
    echo [DEBUG] Environment variables: >> "%LOGFILE%"
    set >> "%LOGFILE%"
)

echo [%date% %time%] Executing: python manage.py start >> "%LOGFILE%"

:: Run the application and capture any errors
python manage.py start >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Application failed to start with error code %ERRORLEVEL% >> "%LOGFILE%"
    echo [ERROR] Application failed to start with error code %ERRORLEVEL%
    echo [ERROR] Check %LOGFILE% for details
    exit /b %ERRORLEVEL%
)

echo [%date% %time%] Application started successfully >> "%LOGFILE%"
echo [SUCCESS] Application started successfully. Log file: %LOGFILE%

endlocal 