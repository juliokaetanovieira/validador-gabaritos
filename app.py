from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from validador_gabaritos import ValidadorProdutos
import glob
from config import config

app = Flask(__name__)

# Função para verificar se a extensão do arquivo é permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Rota principal para a página de upload
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Verifica se o arquivo foi enviado
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        
        # Se o arquivo não tiver nome ou for inválido, retorna um erro
        if file.filename == '' or not allowed_file(file.filename):
            return redirect(request.url)
        
        # Cria o diretório de uploads se não existir
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Salva o arquivo no diretório de uploads
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Captura os logs durante a validação
        logs = []
        
        # Adiciona mensagens de log ao longo da execução
        def log_message(message):
            logs.append(message)
        
        try:
            # Cria um objeto do ValidadorProdutos e executa a validação
            validador = ValidadorProdutos(file_path, log_callback=log_message)
            resultado = validador.executar_validacao_completa()
            
            # Verifica se o resultado é válido
            if not resultado or 'resumo' not in resultado:
                logs.append("❌ Erro: Não foi possível processar o arquivo")
                resultado = None
                
        except Exception as e:
            logs.append(f"❌ Erro durante o processamento: {str(e)}")
            resultado = None

        # Passa os logs para o template
        return render_template('resultado.html', resultado=resultado, logs=logs)
    
    return render_template('index.html')

# Rota para exibir o resultado da validação
@app.route('/resultado')
def resultado():
    return render_template('resultado.html')

if __name__ == '__main__':
    # Obter ambiente da variável de ambiente ou usar development como padrão
    env = os.environ.get('FLASK_ENV', 'development')
    app_config = config.get(env, config['default'])
    
    # Configurar o Flask com as configurações do ambiente
    app.config.from_object(app_config)
    
    print(f"🚀 Iniciando aplicação em modo: {env.upper()}")
    print(f"🌐 Acesso: http://{app_config.HOST}:{app_config.PORT}")
    print(f"📁 Pasta de uploads: {app.config['UPLOAD_FOLDER']}")
    
    app.run(
        host=app_config.HOST,
        port=app_config.PORT,
        debug=app_config.DEBUG
    )
