@echo off
setlocal

echo ========================================================
echo        INSTALADOR DE BIBLIOTECAS DO SCRIPT
echo ========================================================
echo.

echo [1/5] Criando ambiente virtual (venv)...
call python3.13 -m venv venv

echo [2/5] Ativando ambiente virtual...
call venv\Scripts\activate

echo [3/5] Instalando bibliotecas...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/5] Verificando FFmpeg...

if exist "ffmpeg.exe" (
    if exist "ffprobe.exe" (
        echo       FFmpeg ja esta instalado! Pulando download.
        goto :FIM
    )
)

echo       FFmpeg nao encontrado. Baixando automaticamente...
echo       (Aguarde, isso usa o PowerShell para extrair corretamente...)

:: Define URLs e nomes
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "ZIP_NAME=ffmpeg_temp.zip"
set "DIR_NAME=ffmpeg_temp_folder"

:: Baixa o ZIP
curl -L "%FFMPEG_URL%" -o "%ZIP_NAME%"

:: Extrai o ZIP usando PowerShell
echo       Extraindo arquivos (Aguarde)...
powershell -Command "Expand-Archive -Path '%ZIP_NAME%' -DestinationPath '%DIR_NAME%' -Force"

:: Move os arquivos
echo       Configurando FFmpeg...
powershell -Command "Get-ChildItem -Path '%DIR_NAME%' -Recurse -Filter 'ffmpeg.exe' | Move-Item -Destination . -Force"
powershell -Command "Get-ChildItem -Path '%DIR_NAME%' -Recurse -Filter 'ffprobe.exe' | Move-Item -Destination . -Force"

:: Limpeza
echo [5/5] Limpando arquivos temporarios...
if exist "%ZIP_NAME%" del "%ZIP_NAME%"
if exist "%DIR_NAME%" rd /s /q "%DIR_NAME%"

:FIM
echo.
echo ========================================================
echo      INSTALACAO COMPLETA COM SUCESSO!
echo ========================================================
echo.
echo Agora voce pode clicar em "exec-tg-clone.bat" para iniciar.
pause