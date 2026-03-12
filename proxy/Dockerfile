# Nutzen wir ein schlankes Python-Image für den Pi
FROM python:3.11-slim
WORKDIR /app
# Installiert nur die absolut notwendigen Packages
RUN pip install --no-cache-dir flask requests
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]