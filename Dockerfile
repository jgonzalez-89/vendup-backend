# FROM python:3.9-slim-buster

# WORKDIR /app

# COPY requirements.txt .

# RUN pip3 install -r requirements.txt

# COPY . .

# EXPOSE 5000

# CMD ["gunicorn", "--config", "./gunicorn.conf.py", "src.app:app"]
#--------------------------------

# Utiliza la imagen oficial de Python como base
FROM python:3.9-slim

# Establece un directorio de trabajo
WORKDIR /app

# Instalar dependencias para compilar psycopg2
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copia los archivos de requerimientos e instálalos
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia la carpeta src con el código de la aplicación
COPY src/ src/

ENV DATABASE_URL=postgres://vendup_database_user:czJpBXAXvKCbGqDbKNmSVOnX2k4XsnYT@dpg-cg2u29u4dada1e3dgvl0-a.frankfurt-postgres.render.com/vendup_database
ENV FLASK_APP_KEY="any key works"
ENV FLASK_APP=src/app.py
ENV FLASK_DEBUG=1
ENV PIPENV_VERBOSITY=-1
ENV FLASK_STRIPE_KEY="sk_test_51Mf8aTJwZ9bnrLE9ecLR2q1QeoFpuh4A8qCTK8GojuhuYZ8FQNsSYmykb2jrcgH8Rznu8tI9GX8op4sILcUkBUoD00BFItNCIy"
ENV SENDGRID_API_KEY='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'



# Expone el puerto en el que se ejecutará la aplicación
EXPOSE 5000

# Inicia la aplicación con Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.wsgi:app"]
