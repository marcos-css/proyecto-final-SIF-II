# Usar una imagen base de Python oficial
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /code

# Copiar el archivo de requerimientos
COPY ./requirements.txt /code/requirements.txt

# Instalar las dependencias
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copiar el código de la aplicación
COPY ./app /code/app

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
