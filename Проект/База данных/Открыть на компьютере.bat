@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
if exist "..\Начать учиться.html" start "" "..\Начать учиться.html"
if not exist "..\Начать учиться.html" explorer .
