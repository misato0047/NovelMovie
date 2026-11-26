@echo off
chcp 65001 > nul
cd /d "%~dp0"
call _common.bat
set SCENARIO=%~1
if "%SCENARIO%"=="" set SCENARIO=scenario/sample.txt
if exist override.cfg del override.cfg
"%GODOT%" --path . -- "--scenario=%SCENARIO%"
