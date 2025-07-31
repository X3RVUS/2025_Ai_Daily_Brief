FROM python:3.11-slim

# Arbeitsverzeichnis
WORKDIR /app

# Requirements installieren
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektdateien kopieren
COPY app ./app
COPY .env .env

# Port für FastAPI
EXPOSE 8000

# Startbefehl
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
