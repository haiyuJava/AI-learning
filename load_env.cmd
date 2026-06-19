@echo off

set "ENV_FILE=%~1"
if not exist "%ENV_FILE%" exit /b 0

for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
    if not "%%A"=="" (
        set "KEY=%%A"
        set "VALUE=%%B"
        for /f "tokens=* delims= " %%K in ("!KEY!") do set "KEY=%%K"
        for /f "tokens=* delims= " %%V in ("!VALUE!") do set "VALUE=%%V"
        if not "!KEY!"=="" set "!KEY!=!VALUE!"
    )
)
