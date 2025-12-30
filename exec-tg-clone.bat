@echo off
:: Inicia o Python em uma NOVA janela com título "TG Clone"
start "TG Clone" venv\Scripts\python.exe tg-clone.py

:: Quando o robô fechar (ou se houver erro grave), o script volta para cá
exit