@echo off
setlocal enabledelayedexpansion
title Instalador Automatico Python 3.13

echo ========================================================
echo      BAIXANDO E INSTALANDO PYTHON 3.13 AUTOMATICAMENTE
echo ========================================================
echo.

:: 1. Define a URL e o nome do arquivo
set "PYTHON_URL=https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
set "INSTALLER_NAME=python_installer.exe"

:: 2. Verifica se o Python ja existe (opcional, mas bom para evitar reinstalar)
python --version >nul 2>&1
if %errorlevel% EQU 0 (
    echo [AVISO] Python ja parece estar instalado no sistema.
    python --version
    echo.
    set /p REINSTALL="Deseja reinstalar/reparar mesmo assim? (S/N): "
    if /i "!REINSTALL!" NEQ "S" goto :FIM
)

:: 3. Baixa o instalador usando CURL (nativo no Windows 10/11)
echo [1/3] Baixando o instalador do Python 3.13...
curl -L "%PYTHON_URL%" -o "%INSTALLER_NAME%"

if not exist "%INSTALLER_NAME%" (
    echo [ERRO] Falha ao baixar o instalador. Verifique sua internet.
    pause
    exit
)

:: 4. Executa a instalação silenciosa
:: /quiet = Sem interface grafica
:: InstallAllUsers=1 = Instala para todos os usuarios (precisa de Admin)
:: PrependPath=1 = ***ISSO ADICIONA AS VARIAVEIS DE AMBIENTE***
:: Include_pip=1 = Instala o PIP
echo [2/3] Instalando o Python (Isso pode levar alguns minutos)...
echo        Por favor, aguarde e nao feche esta janela.
echo.

"%INSTALLER_NAME%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_pip=1

:: 5. Limpeza
echo [3/3] Limpando arquivos temporarios...
del "%INSTALLER_NAME%"

echo.
echo ========================================================
echo      INSTALACAO CONCLUIDA COM SUCESSO!
echo ========================================================
echo.
echo NOTA: Para que as variaveis de ambiente funcionem, pode ser
echo necessario fechar esta janela e abrir novamente.
echo.

:FIM
echo Pressione qualquer tecla para sair...
pause >nul