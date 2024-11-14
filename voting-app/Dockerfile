# Usar la imagen oficial de Python 3.12
FROM python:3.12-slim


# Establecer el directorio de trabajo en el contenedor
WORKDIR /app


# Copiar los archivos necesarios al contenedor
COPY . .


# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt


# Exponer el puerto que utilizará la aplicación Flask
EXPOSE 5000


# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
