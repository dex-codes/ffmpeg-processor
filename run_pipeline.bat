@echo off
echo.
echo ========================================
echo    VIDEO PROCESSING PIPELINE
echo ========================================
echo.
echo This will run the complete workflow:
echo 1. Generate custom video sequence from CSV
echo 2. Concatenate videos based on the sequence
echo.

REM Check if Python scripts exist
if not exist "generate_my_sequence.py" (
    echo ERROR: Missing generate_my_sequence.py
    pause
    exit /b 1
)

if not exist "video_concatenator.py" (
    echo ERROR: Missing video_concatenator.py
    pause
    exit /b 1
)

echo All required scripts found!
echo.
set /p proceed="Proceed with the complete pipeline? (y/n): "
if /i not "%proceed%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo ========================================
echo    STEP 1: SEQUENCE GENERATION
echo ========================================
echo.
echo Launching sequence generator...
echo Follow the prompts to create your custom sequence
echo.
pause

python generate_my_sequence.py

echo.
echo ========================================
echo    STEP 2: VIDEO CONCATENATION  
echo ========================================
echo.
echo Launching video concatenator...
echo You'll be asked for:
echo - Video directory location
echo - Sequence CSV file (use the one you just generated)
echo - Output settings
echo.
pause

python video_concatenator.py

echo.
echo ========================================
echo    PIPELINE COMPLETE!
echo ========================================
echo.
echo Check your output video file.
echo.
pause
