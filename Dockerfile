# Dockerfile
FROM python:3.11-slim as builder

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio para dependencias
WORKDIR /wheels
COPY requirements.txt .

# Compilar wheels para instalación más rápida
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# ==================== IMAGEN FINAL ====================
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Crear directorio de trabajo
WORKDIR /app

# Copiar wheels desde builder
COPY --from=builder /wheels /wheels

# Instalar dependencias Python desde wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt \
    && rm -rf /wheels

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/data /app/logs /app/temp \
    && chown -R appuser:appuser /app

# Cambiar al usuario no root
USER appuser

# Variables de entorno
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV COOKIES_PATH=/app/data/cookies.txt
ENV LOG_LEVEL=INFO

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio con optimizaciones
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-log", \
     "--log-level", "info"]