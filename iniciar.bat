@echo off
title TCC Qualidade da Agua - Sistema Completo
cls

echo [1/3] A iniciar o Servidor Backend (FastAPI + PostgreSQL)...
cd /d C:\Users\guiil\Software-TCC\backend
start cmd /k "venv\Scripts\Activate && uvicorn main:app --reload"

echo [2/3] A aguardar o servidor estabilizar...
timeout /t 3 /nobreak >nul

echo [3/3] A iniciar o Simulador de Sensores (MQTT)...
cd /d C:\Users\guiil\Software-TCC\backend
start cmd /k "venv\Scripts\Activate && python test_publisher.py"

echo ========================================================
echo   TCC INICIADO COM SUCESSO!
echo   - Backend rodando em: http://127.0.0.1:8000/docs
echo   - As janelas secundarias estao ativas em segundo plano.
echo ========================================================
pause