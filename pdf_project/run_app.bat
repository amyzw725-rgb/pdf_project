@echo off
cd /d "%~dp0"
rem Streamlit / 浏览器
set STREAMLIT_SERVER_HEADLESS=false
rem 下列 LLM 相关变量当前根目录 process_pdfs.py 未读取（仅规则+OCR 管线）。若以后接 Ollama/OpenAPI 可再启用。
rem set INVOICE_LOCAL_LLM_MODEL=qwen3:4b
rem set INVOICE_LLM_TIMEOUT_SEC=600

echo Checking Python packages (install missing if needed)...
py check_imports.py --install
if not errorlevel 1 goto :run_streamlit

python check_imports.py --install
if not errorlevel 1 goto :run_streamlit_py

echo.
echo check_imports.py failed with both py and python.
echo Install everything with:
echo   py -m pip install -r requirements.txt
echo   ... or double-click install_deps.bat
echo.
pause
exit /b 1

:run_streamlit
py -m streamlit run streamlit_app.py --server.headless=false
if not errorlevel 1 goto :end
echo.
echo py failed; trying python...
:run_streamlit_py
python -m streamlit run streamlit_app.py --server.headless=false
if not errorlevel 1 goto :end

echo.
echo Could not run Streamlit.
echo   py -m pip install -r requirements.txt
echo.

:end
pause
