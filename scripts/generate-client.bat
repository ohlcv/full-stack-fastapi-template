@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Generate frontend client code
REM 1. Generate openapi.json from backend
REM 2. Copy to frontend directory
REM 3. Generate TypeScript client code

echo Starting frontend client code generation...

REM Get project root directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%I in ("%SCRIPT_DIR%\..") do set "PROJECT_ROOT=%%~fI"

REM Switch to project root
cd /d "%PROJECT_ROOT%"

REM Check if in project root
if not exist "backend\app\main.py" (
    echo Error: Cannot find project root directory!
    echo   Current directory: %cd%
    echo   Script directory: %SCRIPT_DIR%
    echo   Project root: %PROJECT_ROOT%
    pause
    exit /b 1
)

echo Project root: %cd%

REM Try to generate openapi.json using Docker container
echo Generating openapi.json from backend Docker container...

REM Check if Docker is available
where docker >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed or not in PATH!
    echo Please install Docker: https://www.docker.com/get-started
    pause
    exit /b 1
)

REM Check if backend service is running using docker compose
echo   Checking if backend service is running...
docker compose ps backend --format json 2>nul | findstr /C:"running" >nul 2>&1
if errorlevel 1 (
    echo Error: Backend Docker service is not running!
    echo Please start the backend service: docker compose up -d backend
    pause
    exit /b 1
)

REM Use docker compose exec to run command in backend service (most reliable method)
REM This automatically finds the correct container for the service, regardless of container name
echo   Generating openapi.json using docker compose exec...
set CONTAINER_FOUND=0

REM Try using docker compose exec (recommended method - works regardless of container name)
docker compose exec -T backend python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > "%PROJECT_ROOT%\openapi.json" 2>%TEMP%\openapi_error.txt
if not errorlevel 1 (
    if exist "%PROJECT_ROOT%\openapi.json" (
        for %%A in ("%PROJECT_ROOT%\openapi.json") do (
            if %%~zA gtr 0 (
                echo Success: Generated openapi.json using docker compose exec
                set CONTAINER_FOUND=1
                goto :copy_file
            ) else (
                echo Error: Generated openapi.json is empty!
                if exist "%TEMP%\openapi_error.txt" (
                    echo Error output:
                    type "%TEMP%\openapi_error.txt"
                )
            )
        )
    ) else (
        echo Error: Failed to create openapi.json file!
        if exist "%TEMP%\openapi_error.txt" (
            echo Error output:
            type "%TEMP%\openapi_error.txt"
        )
    )
) else (
    echo Warning: docker compose exec failed, trying fallback method...
    REM Fallback: Find container by name pattern (works with any container name)
    for /f "tokens=*" %%i in ('docker ps --filter "name=backend" --format "{{.Names}}" 2^>nul') do (
        echo   Found container: %%i
        echo   Trying with docker exec...
        docker exec %%i python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > "%PROJECT_ROOT%\openapi.json" 2>%TEMP%\openapi_error.txt
        if not errorlevel 1 (
            if exist "%PROJECT_ROOT%\openapi.json" (
                for %%A in ("%PROJECT_ROOT%\openapi.json") do (
                    if %%~zA gtr 0 (
                        echo Success: Generated openapi.json using docker exec fallback
                        set CONTAINER_FOUND=1
                        goto :copy_file
                    )
                )
            )
        )
    )
    
    if %CONTAINER_FOUND% equ 0 (
        echo Error: Failed to execute Python command in container!
        if exist "%TEMP%\openapi_error.txt" (
            echo Error output:
            type "%TEMP%\openapi_error.txt"
        )
    )
)

REM If container found but generation failed
if %CONTAINER_FOUND% equ 0 (
    echo Error: Failed to generate openapi.json from Docker container!
    echo Please check if the backend container is running correctly.
    echo.
    echo Troubleshooting:
    echo   1. Make sure backend service is running: docker compose ps backend
    echo   2. Check service logs: docker compose logs backend
    echo   3. Try manually: docker compose exec backend python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))"
    pause
    exit /b 1
)

:copy_file
REM Ensure in project root
cd /d "%PROJECT_ROOT%"

REM Check if openapi.json was generated successfully
if not exist "openapi.json" (
    echo Error: openapi.json file was not generated!
    echo   Check path: %cd%\openapi.json
    pause
    exit /b 1
)

REM Copy openapi.json to frontend directory
echo Copying openapi.json to frontend directory...
if not exist "frontend" (
    echo Error: frontend directory not found!
    echo   Current directory: %cd%
    pause
    exit /b 1
)
copy /Y openapi.json frontend\openapi.json >nul

if %errorlevel% neq 0 (
    echo Error: Failed to copy openapi.json!
    echo   Source: %cd%\openapi.json
    echo   Destination: %cd%\frontend\openapi.json
    pause
    exit /b 1
)
echo   Copied to: %cd%\frontend\openapi.json

REM Enter frontend directory
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo Error: Failed to install dependencies!
        cd ..
        pause
        exit /b 1
    )
)

REM Generate client code
echo Generating TypeScript client code...
call npm run generate-client

if %errorlevel% neq 0 (
    echo Error: Failed to generate client code!
    echo   Please check if frontend/openapi.json exists
    cd ..
    pause
    exit /b 1
)

REM Return to project root
cd ..

echo.
echo Client code generation completed!
echo.
echo Generated files:
echo   - openapi.json: %cd%\frontend\openapi.json
echo   - TypeScript types: %cd%\frontend\src\client\types.gen.ts
echo   - TypeScript Schema: %cd%\frontend\src\client\schemas.gen.ts
echo   - SDK code: %cd%\frontend\src\client\sdk.gen.ts
echo.
pause
