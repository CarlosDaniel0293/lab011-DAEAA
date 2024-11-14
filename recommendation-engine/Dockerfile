# Usar una imagen base de Python
FROM python:3.12-slim


# Establecer el directorio de trabajo
WORKDIR /app


# Copiar los archivos de la aplicación
COPY recommendation.py /app/


# Instalar dependencias
RUN pip install Flask requests scikit-learn


# Exponer el puerto 5001
EXPOSE 5001


# Comando para ejecutar la aplicación
CMD ["python", "recommendation.py"]