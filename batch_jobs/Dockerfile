FROM python:3.9-slim-bullseye

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR /app

COPY . .

ENTRYPOINT [ "python", "main.py" ]