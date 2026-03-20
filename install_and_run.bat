@echo off
echo ============================================
echo   Object Dimension Detector - Setup + Run
echo ============================================

REM Activate conda env if it exists, else use base
call conda activate obj-detect 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo [INFO] 'obj-detect' env not found - using base env
    call conda activate base 2>nul
)

cd /d "%~dp0"

echo.
echo [1/2] Installing dependencies...
pip install opencv-python==4.9.0.80 numpy==1.26.4 matplotlib==3.8.4 imutils==0.5.4 Pillow==10.3.0 scipy==1.13.0 --quiet

echo.
echo [2/2] Generating test images and running detector...
python generate_test_images.py
python run_all_tests.py

echo.
echo Done! Check the test_images folder for *_result.jpg output files.
pause
