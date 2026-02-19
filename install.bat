@echo off
echo ========================================
echo OptiScam Installation Script
echo ========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

REM Check FFmpeg
echo Checking FFmpeg installation...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo WARNING: FFmpeg not found!
    echo FFmpeg is required for audio extraction.
    echo.
    echo Install options:
    echo   1. Using Chocolatey: choco install ffmpeg
    echo   2. Using Scoop: scoop install ffmpeg
    echo   3. Download from: https://ffmpeg.org/download.html
    echo.
    set /p continue="Continue without FFmpeg? (y/n): "
    if /i not "%continue%"=="y" (
        exit /b 1
    )
) else (
    echo FFmpeg found!
)
echo.

REM Install Python packages
echo Installing Python packages...
echo This may take several minutes...
echo.
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Package installation failed!
    echo Try manually: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Run setup verification: python setup.py
echo   2. Analyze a video: python main.py video.mp4
echo   3. See examples: python example_usage.py
echo   4. Read documentation: README.md
echo.
pause
