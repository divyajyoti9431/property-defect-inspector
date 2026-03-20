@echo off
echo ================================================
echo   Push Object Dimension Detector to GitHub
echo ================================================
echo.

cd /d "%~dp0"

REM Check git
git --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed. Download from https://git-scm.com/
    pause & exit /b 1
)

REM Check gh CLI
gh --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] GitHub CLI (gh) not found.
    echo         Install from: https://cli.github.com/
    echo         Then run: gh auth login
    pause & exit /b 1
)

REM Check auth
gh auth status >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [AUTH] Not logged in to GitHub. Starting login...
    gh auth login
)

echo [1/5] Initialising local git repository...
git init
git branch -M main

echo [2/5] Staging all project files...
git add detector.py
git add detect_realistic.py
git add generate_test_images.py
git add run_all_tests.py
git add install_and_run.py
git add environment.yml
git add README.md
git add .gitignore

echo [3/5] Creating first commit...
git commit -m "Initial commit: Object Dimension Detector using OpenCV

- Multi-scale Canny segmentation for object detection
- Hough Circles for round holes
- Contour hierarchy for slots/rectangular holes
- Pixel-per-mm calibration for real-world measurements
- Webcam capture, image file, and demo modes
- Realistic industrial part detector

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

echo [4/5] Creating GitHub repository and pushing...
gh repo create object-dimension-detector ^
    --public ^
    --description "Computer vision prototype to detect object width, height and hole dimensions using OpenCV" ^
    --push ^
    --source .

echo.
echo [5/5] Verifying...
gh repo view --web

echo.
echo ================================================
echo   SUCCESS! Repository is live on GitHub.
echo ================================================
pause
