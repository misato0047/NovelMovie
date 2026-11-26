@echo off
chcp 65001 > nul
cd /d "%~dp0"
call _common.bat
set SCENARIO=%~1
if "%SCENARIO%"=="" set SCENARIO=scenario/sample.txt
for %%F in ("%SCENARIO%") do set NAME=%%~nF
if not exist out mkdir out
if exist override.cfg del override.cfg
echo [1/2] 文字なし・横長(16:9)で書き出し中: %NAME%
"%GODOT%" --path . --write-movie "out\%NAME%_16x9_notext.avi" -- "--scenario=%SCENARIO%" --notext
copy /Y formats\vertical.cfg override.cfg > nul
echo [2/2] 文字なし・縦長(9:16)で書き出し中: %NAME%
"%GODOT%" --path . --write-movie "out\%NAME%_9x16_notext.avi" -- "--scenario=%SCENARIO%" --notext
del override.cfg
echo 完了: out フォルダを確認してください
pause
