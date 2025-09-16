# Usamos una imagen base ligera de Python
FROM python:3.9-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el archivo de requerimientos e instalamos las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código de la aplicación
COPY app.py .

# Exponemos el puerto en el que corre Flask
EXPOSE 5000

# Comando para ejecutar la aplicación al iniciar el contenedor
CMD ["python", "app.py"]