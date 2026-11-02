@echo off
REM Build hayday-bot.exe tren Windows.
REM Yeu cau: Python 3.10+ trong PATH da cai requirements.txt + pyinstaller
cd /d "%~dp0"

python -m PyInstaller --noconfirm --clean hayday-bot.spec
if errorlevel 1 goto :err

echo.
echo Xong: dist\hayday-bot.exe
echo Chay thu: dist\hayday-bot.exe --sim --cycles 2
goto :eof

:err
echo Build that bai - kiem tra thong bao loi o tren.
exit /b 1
