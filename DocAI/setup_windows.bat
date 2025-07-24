@echo off
echo ===================================
echo DocAI Windows Setup
echo ===================================
echo.
echo Choose deployment method:
echo 1. Vagrant (Recommended)
echo 2. Docker
echo.
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" goto vagrant
if "%choice%"=="2" goto docker
goto end

:vagrant
echo.
echo Setting up with Vagrant...
where /q vagrant
IF ERRORLEVEL 1 (
    echo ERROR: Vagrant not found!
    echo Please install from: https://www.vagrantup.com/
    pause
    exit /b 1
)
vagrant up
echo.
echo Vagrant setup complete!
echo Access DocAI at: http://localhost:8080
goto end

:docker
echo.
echo Setting up with Docker...
where /q docker
IF ERRORLEVEL 1 (
    echo ERROR: Docker not found!
    echo Please install Docker Desktop from: https://www.docker.com/
    pause
    exit /b 1
)
docker-compose up -d
echo.
echo Docker setup complete!
echo Access DocAI at: http://localhost:8080
goto end

:end
pause