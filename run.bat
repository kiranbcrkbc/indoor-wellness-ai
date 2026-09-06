@echo off
title Indoor Wellness and Smart Shelf AI System
echo ====================================================================
echo   INDOOR WELLNESS & SMART SHELF AI SYSTEM - SOFTWARE PLATFORM
echo   Software-Only Demonstration (Zero Hardware Dependency)
echo ====================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    echo Starting application using virtual environment...
    ".venv\Scripts\python.exe" run.py
) else (
    echo Virtual environment not found. Attempting to run with system python...
    python run.py
)

pause
