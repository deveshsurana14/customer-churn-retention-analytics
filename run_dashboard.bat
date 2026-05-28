@echo off
title Customer Churn Intelligence Dashboard
echo.
echo  ============================================
echo   Customer Churn Intelligence Dashboard
echo  ============================================
echo.

cd /d "%~dp0"

echo  Checking Python environment...
call venv\Scripts\activate.bat

echo  Installing dashboard dependencies (first run only)...
pip install streamlit plotly --quiet

echo.
echo  Starting dashboard... (a browser tab will open automatically)
echo  Press Ctrl+C in this window to stop.
echo.

streamlit run dashboard\app.py --server.headless false --browser.gatherUsageStats false

pause
