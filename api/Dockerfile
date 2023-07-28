# https://cloud.google.com/run/docs/tips/python
FROM python:3.9-slim

ENV PYTHONUNBUFFERED True

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

# if we have multiple workers then we need to download the cached models again
CMD exec gunicorn --bind :$PORT --workers 1 --threads 30 --timeout 0 app:app
