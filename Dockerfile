FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "src/app.py"]

# FROM alpine:latest
# RUN apk update
# RUN apk add py-pip
# RUN apk add --no-cache python3-dev 
# RUN pip install --upgrade pip
# WORKDIR /app
# COPY . /app
# RUN pip --no-cache-dir install -r requirements.txt
# CMD ["python3", "src/app.py"]