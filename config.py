import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente baseado no ambiente atual
env = os.environ.get('FLASK_ENV', 'development')
env_file = f'.env.{env}'
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()  # Fallback para .env padrão

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-validador-2024'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # Configurações de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    
    # Configurações de segurança
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    DEBUG = True
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 5000))
    ENV = 'development'
    LOG_LEVEL = 'DEBUG'
    SESSION_COOKIE_SECURE = False

class StagingConfig(Config):
    DEBUG = False
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    ENV = 'staging'
    LOG_LEVEL = 'INFO'
    SESSION_COOKIE_SECURE = True
    
    # Validações específicas para staging
    @classmethod
    def validate_config(cls):
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY é obrigatória em staging")

class ProductionConfig(Config):
    DEBUG = False
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 80))
    ENV = 'production'
    LOG_LEVEL = 'WARNING'
    SESSION_COOKIE_SECURE = True
    
    # Configurações específicas de produção
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    
    @classmethod
    def validate_config(cls):
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise ValueError(f"Variáveis obrigatórias em produção: {', '.join(missing)}")

config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}