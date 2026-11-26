@echo off
chcp 65001 > nul
cd /d "%~dp0"
call _common.bat
set SCENARIO=%~1
if "%SCENARIO%"=="" set SCENARIO=scenario/sample.txt
copy /Y formats\vertical.cfg override.cfg > nul
"%GODOT%" --path . -- "--scenario=%SCENARIO%"
del override.cfg
