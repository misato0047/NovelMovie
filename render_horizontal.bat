@echo off
chcp 65001 > nul
cd /d "%~dp0"
call _common.bat
set SCENARIO=%~1
if "%SCENARIO%"=="" set SCENARIO=scenario/sample.txt
for %%F in ("%SCENARIO%") do set NAME=%%~nF
if not exist out mkdir out
if exist override.cfg del override.cfg
echo 横長(16:9)で書き出し中: %NAME%
"%GODOT%" --path . --write-movie "out\%NAME%_16x9.avi" -- "--scenario=%SCENARIO%"
echo 完了: out\%NAME%_16x9.avi
pause
