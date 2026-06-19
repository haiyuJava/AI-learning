@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "ENV_FILE=%ROOT%.env.local"
if exist "%ENV_FILE%" call "%ROOT%load_env.cmd" "%ENV_FILE%"

set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON="
if not defined PYTHON (
    where py >nul 2>nul
    if not errorlevel 1 set "PYTHON=py -3"
)
if not defined PYTHON (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON=python"
)
if not defined PYTHON (
    echo Python not found. Create .venv or install Python.
    exit /b 1
)

set "MODULE=%~1"
shift
set "ARGS="
:collect_args
if "%~1"=="" goto :invoke
if defined ARGS (
    set "ARGS=%ARGS% %1"
) else (
    set "ARGS=%1"
)
shift
goto collect_args
:invoke
%PYTHON% -m %MODULE% %ARGS%
exit /b %errorlevel%
