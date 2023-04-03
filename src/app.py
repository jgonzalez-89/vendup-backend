import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from src.api.utils import APIException, generate_sitemap
from src.api.models import db, User
from src.api.routes import api
from src.api.admin import setup_admin
from src.api.commands import setup_commands
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_bcrypt import Bcrypt
from datetime import timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer


ENV = os.getenv("FLASK_DEBUG")
static_file_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../public/"
)

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.url_map.strict_slashes = False

app.config["JWT_SECRET_KEY"] = "jwt-secret-string"
jwt = JWTManager(app)

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace(
        "postgres://", "postgresql://"
    )
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

CORS(app)

setup_admin(app)

setup_commands(app)

app.register_blueprint(api, url_prefix="/api")

app.config['SENDGRID_API_KEY'] = os.environ.get('SENDGRID_API_KEY')
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def send_confirmation_email(user_email, token):
    # Personaliza el remitente del correo electrónico
    from_email = "register.vendup@gmail.com"
    to_email = user_email
    # Personaliza el asunto del correo electrónico
    subject = "Confirmación de registro en Vendup"
    confirmation_url = url_for("confirm_email", token=token, _external=True)
    # Agrega la URL de la imagen que deseas mostrar
    image_url = "https://i.ibb.co/FKYfNK8/vendup-6ff606c6.png"
    content = f"""\
Hola,
<br>
<img src="{image_url}" alt="Vendup img">
<br>
Gracias por registrarte en Vendup. Para confirmar tu cuenta, por favor haz clic en el siguiente enlace:
<br>
<br>
<br>
<a href="{confirmation_url}">{confirmation_url}</a><br>
<br>
<br>
<br>
Si no solicitaste este registro, por favor ignora este correo electrónico.
<br>
<br>
Saludos cordiales,
El equipo de Vendup
<br>
<br>
Este es un correo electrónico automático, por favor no responda.
"""
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=content,
    )

    try:
        sg = SendGridAPIClient(app.config["SENDGRID_API_KEY"])
        response = sg.send(message)
        print(response.status_code)
        return response.status_code
    except Exception as e:
        print(e)
        return None


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


@app.route("/register", methods=["POST"])
def register():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    if not email or not password:
        return jsonify({"message": "Missing email or password", "status": 400})

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Email already registered", "status": 400})

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(email=email, hash=hashed_password, is_active=False)
    db.session.add(new_user)
    db.session.commit()

    token = serializer.dumps(new_user.email, salt="email-confirm")
    send_confirmation_email(new_user.email, token)

    return jsonify({
        "message": "Registered successfully. Please check your email to confirm your account.",
        "status": 200
    })


@app.route("/confirm-email/<token>", methods=["GET"])
def confirm_email(token):
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=3600)
    except Exception as e:
        return jsonify({"message": "Invalid or expired token", "status": 400})

    user = User.query.filter_by(email=email).first()

    if user.is_active:
        return jsonify({"message": "Account already confirmed", "status": 200})

    user.is_active = True
    db.session.commit()

    return """
        <html>
        <head>
            <title>Confirmation Success</title>
            <script>
                setTimeout(() => {
                    window.close();
                }, 3000); // 3 segundos de demora antes de cerrar la ventana
            </script>
        </head>
        <body>
            <h1>¡Gracias por confirmar tu cuenta!</h1>
            <p>Tu cuenta ha sido confirmada exitosamente.</p>
        </body>
        </html>
    """


@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    if not email or not password:
        return jsonify({"message": "Missing email or password", "status": 400})

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found", "status": 404})

    if not bcrypt.check_password_hash(user.hash, password):
        return jsonify({"message": "Invalid email or password", "status": 401})

    if not user.is_active:
        return jsonify({"message": "Inactive user", "status": 401})

    access_token = create_access_token(
        identity=user.id, expires_delta=timedelta(minutes=30))

    return jsonify({
        "message": "Logged in successfully",
        "access_token": access_token
    })


@app.route("/")
def sitemap():
    if ENV == "1":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, "index.html")


@app.route("/<path:path>", methods=["GET"])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = "index.html"
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # avoid cache memory
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
