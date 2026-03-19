@echo off
:: ================================================================
:: PYTHON SCRIPT LAUNCHER (Light Mode)
:: ================================================================

:LAUNCHER_START

:: Enable UTF-8 encoding (important for arrows, lines, emojis)
chcp 65001 >nul

title Python Script Launcher (Light Mode)

cls
echo.
echo ==============================
echo    Python Script Launcher
echo ==============================
echo.

setlocal enabledelayedexpansion
set count=0

:: Detect all .py files
for %%f in (*.py) do (
    set /a count+=1
    set "file[!count!]=%%f"
    echo  !count!. %%f
)

if %count%==0 (
    echo ❌ No Python files found in this folder.
    pause
    exit /b
)

echo.
set /p choice=👉 Enter the number of the script to run: 

if not defined file[%choice%] (
    echo ❌ Invalid selection.
    pause
    exit /b
)

set "selected=!file[%choice%]!"

echo.
echo 🚀 Running: !selected!
echo.

:: Enable UTF-8 for Python
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

python "!selected!"

echo.
echo ==============================
echo        ✔ Script Finished
echo ==============================
echo.

echo What do you want to do next?
echo.
echo 1. 🔁 Run another script
echo 2. ❌ Exit
echo.

set /p nextchoice=👉 Enter your choice: 

if "%nextchoice%"=="1" (
    goto LAUNCHER_START
)

if "%nextchoice%"=="2" (
    exit /b
)

:: If invalid → exit safely
exit /b
