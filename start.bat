@echo off
setlocal
title IQ Analyzer - LTE Cell Detection Engine

echo 📡 Starting IQ Analyzer...
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python and try again.
    pause
    exit /b
)

:: 2. Check for dependencies (Silent update)
echo [1/3] Checking dependencies...
pip install -r req.txt >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Could not verify dependencies. Ensure you have an internet connection.
)

:: 3. Attempt to build C++ Accelerated Engine (Optional)
echo [2/3] Checking C++ acceleration...
if not exist "cpp\build\Release\lte_engine.dll" (
    echo [INFO] C++ library not found. Attempting to build for 100x speedup...
    echo [NOTE] This requires CMake and Visual Studio. Skip if not installed.
    pushd cpp
    if exist "C:\Program Files\CMake\bin\cmake.exe" set "CMAKE_PATH=C:\Program Files\CMake\bin\cmake.exe"
    where cmake >nul 2>nul && set "CMAKE_PATH=cmake"
    
    if defined CMAKE_PATH (
        mkdir build >nul 2>nul
        cd build
        %CMAKE_PATH% .. >nul 2>nul
        %CMAKE_PATH% --build . --config Release >nul 2>nul
    ) else (
        echo [INFO] CMake not detected. Running in standard Python mode.
    )
    popd
) else (
    echo [OK] C++ engine is ready!
)

:: 4. Start the Application
echo [3/3] Launching Web Dashboard...
echo.
echo Dashboard will be available at: http://localhost:5000
echo.
python app.py

pause
