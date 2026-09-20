@echo off
title EvoVariant Web Platform
echo ========================================================
echo Starting EvoVariant-TR Next.js Platform on port 3000...
echo Connecting to Modal H100 Cloud GPU (Evo 2 7B)...
echo ========================================================
cd /d "%~dp0apps\web"
start http://localhost:3000
node ./node_modules/next/dist/bin/next dev -p 3000
pause
