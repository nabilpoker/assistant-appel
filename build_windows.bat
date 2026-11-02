@echo off
REM Génère Damia.exe. À lancer sur un PC Windows avec Python 3.11+.
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name Damia --collect-all webview --add-data "index.html;." --add-data "logo.svg;." launcher.py
echo.
echo Termine. Le fichier est dans dist\Damia.exe
pause
