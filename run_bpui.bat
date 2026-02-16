@echo off
REM Launcher script for Blueprint UI (Windows)

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

REM Check if venv exists
if not exist "%VENV_PYTHON%" (
    echo Virtual environment not found. Setting up...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo Make sure Python 3.8+ is installed and in your PATH.
        pause
        exit /b 1
    )
    
    call "%VENV_DIR%\Scripts\activate.bat"
    
    echo Installing dependencies...
    python -m pip install --quiet --upgrade pip
    if errorlevel 1 (
        echo WARNING: pip upgrade failed, continuing anyway...
    )
    
    REM Install from requirements.txt if it exists
    if exist "%SCRIPT_DIR%requirements.txt" (
        pip install --quiet -r "%SCRIPT_DIR%requirements.txt"
        if errorlevel 1 (
            echo ERROR: Failed to install dependencies from requirements.txt
            pause
            exit /b 1
        )
    ) else (
        REM Fallback to manual installation
        pip install --quiet textual rich tomli-w httpx setuptools wheel PySide6
        if errorlevel 1 (
            echo ERROR: Failed to install base dependencies
            pause
            exit /b 1
        )
        
        REM Add tomli for Python ^< 3.11
        python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
        if errorlevel 1 (
            pip install --quiet tomli
        )
    )
    
    echo Installing bpui in editable mode...
    pip install --quiet -e "%SCRIPT_DIR%."
    if errorlevel 1 (
        echo ERROR: Failed to install bpui
        pause
        exit /b 1
    )
    
    echo.
    echo Setup complete!
    echo.
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

REM Check for updates to dependencies
if "%1"=="--update-deps" (
    echo Updating dependencies...
    python -m pip install --quiet --upgrade pip
    if exist "%SCRIPT_DIR%requirements.txt" (
        pip install --quiet --upgrade -r "%SCRIPT_DIR%requirements.txt"
    )
    pip install --quiet -e "%SCRIPT_DIR%."
    echo Dependencies updated!
    echo.
    shift
)

REM Run bpui with remaining arguments
python -m bpui.core.cli %*

endlocal