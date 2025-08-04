# Basis-Image
FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektdateien kopieren
# Der Anwendungscode liegt im Unterordner `app`, wird aber direkt ins
# Arbeitsverzeichnis kopiert, damit `uvicorn` das Modul `main` ohne
# Paketpräfix finden kann.
COPY app/ .

# Expose für FastAPI
EXPOSE 8000

# Startbefehl für FastAPI
# Durch das direkte Kopieren nach `/app` liegt `main.py` im
# Arbeitsverzeichnis. Daher starten wir `uvicorn` auf `main:app`.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
