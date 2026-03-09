@echo off
REM Launcher script for Character Generator Desktop (Windows)

setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "API_HOST=127.0.0.1"
set "API_PORT=8000"
set "API_URL=http://%API_HOST%:%API_PORT%/api/health"
set "API_PID="

call :require_command python "Install Python 3.10+ and make sure it is on your PATH."
if errorlevel 1 exit /b 1

call :require_command pnpm "Install pnpm 9+ and make sure it is on your PATH."
if errorlevel 1 exit /b 1

call :require_command cargo "Install Rust/Cargo; Tauri needs a Rust toolchain."
if errorlevel 1 exit /b 1

call :require_command curl "Install curl so the launcher can detect when the API is ready."
if errorlevel 1 exit /b 1

call :ensure_python_env
if errorlevel 1 goto :cleanup_and_fail

if "%~1"=="--update-deps" (
    echo Updating Python and Node dependencies...
    python -m pip install --quiet --upgrade pip || goto :cleanup_and_fail
    if exist "%SCRIPT_DIR%requirements.txt" (
        pip install --quiet --upgrade -r "%SCRIPT_DIR%requirements.txt" || goto :cleanup_and_fail
    )
    pip install --quiet -e "%SCRIPT_DIR%." || goto :cleanup_and_fail
    call pnpm install || goto :cleanup_and_fail
    echo ^✓ Dependencies updated
    shift
)

call :ensure_node_deps
if errorlevel 1 goto :cleanup_and_fail

call :stop_existing_api
if errorlevel 1 goto :cleanup_and_fail

echo Starting API server on %API_HOST%:%API_PORT%...
start "Character Generator API" /B cmd /c "cd /d ""%SCRIPT_DIR%"" && ""%VENV_PYTHON%"" -m uvicorn bpui.api.main:app --host %API_HOST% --port %API_PORT%"

call :capture_api_pid
if errorlevel 1 goto :cleanup_and_fail

call :wait_for_api
if errorlevel 1 goto :cleanup_and_fail

echo Launching desktop app...
cd /d "%SCRIPT_DIR%"
call pnpm tauri:dev %*
set "LAUNCH_EXIT=%ERRORLEVEL%"
goto :cleanup_and_exit

:require_command
where %~1 >nul 2>&1
if errorlevel 1 (
    echo Error: '%~1' is required. %~2
    exit /b 1
)
exit /b 0

:ensure_python_env
if not exist "%VENV_PYTHON%" (
    echo Virtual environment not found. Setting up...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )

    call "%VENV_DIR%\Scripts\activate.bat"

    echo Installing Python dependencies...
    python -m pip install --quiet --upgrade pip || exit /b 1
    if exist "%SCRIPT_DIR%requirements.txt" (
        pip install --quiet -r "%SCRIPT_DIR%requirements.txt" || exit /b 1
    ) else (
        pip install --quiet textual rich tomli-w httpx setuptools wheel PySide6 || exit /b 1
        python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
        if errorlevel 1 pip install --quiet tomli || exit /b 1
    )
    pip install --quiet -e "%SCRIPT_DIR%." || exit /b 1
    echo ^✓ Python environment ready
    exit /b 0
)

call "%VENV_DIR%\Scripts\activate.bat"
exit /b 0

:ensure_node_deps
if not exist "%SCRIPT_DIR%node_modules" (
    echo Node dependencies not found. Installing with pnpm...
    call pnpm install || exit /b 1
    echo ^✓ Node dependencies installed
)
exit /b 0

:stop_existing_api
set "FOUND_CONFLICT="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "Get-CimInstance Win32_Process ^| Where-Object { $_.CommandLine -match 'uvicorn bpui\.api\.main:app' } ^| ForEach-Object { $_.ProcessId }"`) do (
    set "OLD_PID=%%P"
    if not "!OLD_PID!"=="" (
        call :process_listens_on_port !OLD_PID!
        if !errorlevel! EQU 0 (
            echo Restarting existing local API process on port %API_PORT%...
            taskkill /PID !OLD_PID! /T /F >nul 2>&1
        )
    )
)

for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$connections = Get-NetTCPConnection -State Listen -LocalPort %API_PORT% -ErrorAction SilentlyContinue; if ($connections) { $connections | Select-Object -ExpandProperty OwningProcess -Unique }"`) do (
    set "PORT_PID=%%P"
    if not "!PORT_PID!"=="" (
        call :is_repo_api_process !PORT_PID!
        if errorlevel 1 (
            echo Error: Port %API_PORT% is already in use by a non-bpui process.
            powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter 'ProcessId = !PORT_PID!' | Select-Object ProcessId, CommandLine | Format-List"
            exit /b 1
        )
        taskkill /PID !PORT_PID! /T /F >nul 2>&1
    )
)
exit /b 0

:process_listens_on_port
set "CHECK_PID=%~1"
powershell -NoProfile -Command "$match = Get-NetTCPConnection -State Listen -LocalPort %API_PORT% -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -eq %CHECK_PID% }; if ($match) { exit 0 } else { exit 1 }"
exit /b %ERRORLEVEL%

:is_repo_api_process
set "CHECK_PID=%~1"
powershell -NoProfile -Command "$proc = Get-CimInstance Win32_Process -Filter 'ProcessId = %CHECK_PID%'; if ($proc -and $proc.CommandLine -match 'uvicorn bpui\.api\.main:app') { exit 0 } else { exit 1 }"
exit /b %ERRORLEVEL%

:capture_api_pid
set "API_PID="
for /l %%I in (1,1,20) do (
    for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "Get-CimInstance Win32_Process ^| Where-Object { $_.CommandLine -match 'uvicorn bpui\.api\.main:app' } ^| Sort-Object CreationDate -Descending ^| Select-Object -First 1 -ExpandProperty ProcessId"`) do (
        set "API_PID=%%P"
    )
    if defined API_PID exit /b 0
    timeout /t 1 /nobreak >nul
)

echo Error: Failed to locate the API server process after launch.
exit /b 1

:wait_for_api
for /l %%I in (1,1,30) do (
    curl -fsS "%API_URL%" >nul 2>&1 && exit /b 0

    if defined API_PID (
        tasklist /FI "PID eq %API_PID%" | find "%API_PID%" >nul 2>&1
        if errorlevel 1 (
            echo Error: API server exited before becoming ready.
            exit /b 1
        )
    )

    timeout /t 1 /nobreak >nul
)

echo Error: API server did not become ready at %API_URL%
exit /b 1

:cleanup_and_fail
set "LAUNCH_EXIT=1"
goto :cleanup_and_exit

:cleanup_and_exit
if defined API_PID (
    tasklist /FI "PID eq %API_PID%" | find "%API_PID%" >nul 2>&1
    if not errorlevel 1 (
        taskkill /PID %API_PID% /T /F >nul 2>&1
    )
)

endlocal & exit /b %LAUNCH_EXIT%