from flask import Flask

def create_app():
    app = Flask(__name__)

    # Configuración de la aplicación

    # Registro de blueprints
    from .routes import api
    app.register_blueprint(api, url_prefix='/api')

    return app