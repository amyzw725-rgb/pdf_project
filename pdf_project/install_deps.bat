@echo off
cd /d "%~dp0"
echo Installing packages from requirements.txt ...
py -m pip install -r requirements.txt
if not errorlevel 1 goto :done
python -m pip install -r requirements.txt
if not errorlevel 1 goto :done
echo pip failed with both py and python.
:done
pause
