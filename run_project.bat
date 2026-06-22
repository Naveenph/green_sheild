@echo off
echo ==================================================
echo       Green Shield - Automated Setup Script
echo ==================================================
echo.

:: Step 1: Check for .env file
if not exist ".env" (
    echo [!] .env file not found. Creating one from .env.example...
    copy .env.example .env
    echo [!] PLEASE REMEMBER TO ADD YOUR API KEYS TO .ENV LATER!
)

:: Step 2: Create virtual environment if it doesn't exist
echo.
echo === STEP 1: Checking Virtual Environment ===
if not exist "venv" (
    echo Creating a new virtual environment...
    python -m venv venv
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists. Skipping creation.
)

:: Step 3: Activate and Install Requirements
echo.
echo === STEP 2: Installing Dependencies ===
echo Activating environment and installing required libraries...
echo (This may take a few minutes if TensorFlow needs to be downloaded)
call venv\Scripts\activate.bat
pip install -r requirements.txt

:: Step 4: Database Setup Warning
echo.
echo === STEP 3: Database Setup ===
echo.
echo [!] IMPORTANT CHECK FOR XAMPP USERS [!]
echo If you are using XAMPP for your database:
echo 1. Open XAMPP Control Panel
echo 2. Start Apache and MySQL
echo 3. Open phpMyAdmin and create an empty database named: greenshield_db
echo.
echo (If you are NOT using XAMPP, ignore the warning above. SQLite will be used).
echo.
pause

:: Step 5: Initialize DB
echo.
echo Initializing database...
python scripts\setup_db.py

:: Step 6: Start the App
echo.
echo === STEP 4: Starting Green Shield Server ===
python main_server.py

pause
