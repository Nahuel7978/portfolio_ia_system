FROM python:3.10-slim

WORKDIR /app

# Evita que Python escriba archivos .pyc y fuerza salida por consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer el puerto
EXPOSE 8001

# Comando para iniciar FastAPI
CMD ["uvicorn", "src.API.api_main:app", "--host", "0.0.0.0", "--port", "8001"]