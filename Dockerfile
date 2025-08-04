FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Crear usuario no root
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorio para cookies y logs
RUN mkdir -p /app/data /app/logs \
    && chown -R app:app /app/data /app/logs

# Cambiar al usuario no root
USER app

# Exponer puerto
EXPOSE 8000

# Variables de entorno por defecto
ENV PYTHONPATH=/app
ENV COOKIES_PATH=/app/data/cookies.txt

# Comando por defecto
CMD ["python", "main.py"]