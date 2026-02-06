# ==============================================
# Dockerfile para Apotheclean Backend
# ==============================================
# Imagen base con Python 3.14 usando uv para gestión de dependencias

FROM python:3.14-slim AS base

# Metadatos
LABEL maintainer="Juan" \
      description="Backend API para sistema de farmacia Apotheclean" \
      version="0.1.0"

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Directorio de trabajo
WORKDIR /app

# ==============================================
# Etapa de construcción
# ==============================================
FROM base AS builder

# Instalar uv
RUN pip install uv

# Copiar archivos de dependencias
COPY pyproject.toml uv.lock ./

# Instalar dependencias con uv
RUN uv sync --frozen --no-dev

# ==============================================
# Etapa de producción
# ==============================================
FROM base AS production

# Crear usuario no-root por seguridad
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash appuser

# Copiar entorno virtual desde builder
COPY --from=builder /app/.venv /app/.venv

# Agregar venv al PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copiar código fuente
COPY src/ ./src/
COPY scripts/ ./scripts/

# Crear directorio para datos persistentes (SQLite)
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Puerto expuesto
EXPOSE 5000

# Comando de inicio
CMD ["python", "-m", "src.main"]
