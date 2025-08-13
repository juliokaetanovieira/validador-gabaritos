@echo off
echo 🚀 Iniciando deploy para STAGING...

REM Define o ambiente
set FLASK_ENV=staging

REM Ativa o ambiente virtual (se existir)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Instala dependências
pip install -r requirements.txt

REM Executa testes (se existirem)
echo 🧪 Executando testes...
python -m pytest tests/ || echo ⚠️  Testes falharam, mas continuando...

REM Inicia a aplicação
echo 🌐 Iniciando aplicação em modo STAGING...
python app.py

pause