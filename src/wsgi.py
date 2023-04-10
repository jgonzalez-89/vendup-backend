

from dotenv import load_dotenv
load_dotenv()

# Aquí es donde creas la instancia de tu aplicación, por ejemplo:
from src.app import app

if __name__ == '__main__':
    app.run()