FROM python:3.9

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . /app/

CMD gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8000