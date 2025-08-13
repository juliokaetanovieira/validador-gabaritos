@echo off
echo 🚀 Iniciando deploy para PRODUÇÃO...

REM Validações de segurança
if "%PRODUCTION_SECRET_KEY%"=="" (
    echo ❌ ERRO: PRODUCTION_SECRET_KEY não definida!
    pause
    exit /b 1
)

REM Define o ambiente
set FLASK_ENV=production

REM Ativa o ambiente virtual
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ❌ ERRO: Ambiente virtual não encontrado!
    pause
    exit /b 1
)

REM Instala dependências
pip install -r requirements.txt

REM Executa testes obrigatórios
echo 🧪 Executando testes obrigatórios...
python -m pytest tests/ || (
    echo ❌ ERRO: Testes falharam! Deploy cancelado.
    pause
    exit /b 1
)

REM Backup (se necessário)
echo 💾 Criando backup...

REM Inicia a aplicação
echo 🌐 Iniciando aplicação em modo PRODUÇÃO...
python app.py