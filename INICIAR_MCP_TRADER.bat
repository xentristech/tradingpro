@echo off
title MCP TRADER 24/7 - XENTRISTECH
cls

echo ===============================================
echo      XENTRISTECH - MCP TRADER 24/7 CONSOLE
echo ===============================================
echo.
echo Iniciando consola MCP Trader...
echo.

REM Intentar con python o py
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py -3 src\ui\mcp_trader_terminal.py
) else (
    python src\ui\mcp_trader_terminal.py
)

pause

