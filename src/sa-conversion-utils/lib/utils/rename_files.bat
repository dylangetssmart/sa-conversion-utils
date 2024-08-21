@echo off
setlocal enabledelayedexpansion

rem Change to the directory where your .SQL files are located
cd /d "C:\LocalConv\Needles-Skolrood\sql-scripts\conv"

rem Loop through all files with .SQL extension
for %%f in (*.SQL) do (
    rem Get the file name without extension
    set "name=%%~nf"
    rem Rename the file to have .sql extension
    ren "%%f" "!name!.sql"
)

echo All files have been renamed from .SQL to .sql
pause
