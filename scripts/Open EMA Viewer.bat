@echo off
cd /d "%~dp0.."
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
start "" streamlit run "streamlit_app.py"
