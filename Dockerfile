# Starts from the official Python 3.13 image
FROM python:3.13-slim

# Installs libexpat1, a system library. Rasterio uses GDAL underneath, and GDAL needs this library. The slim image doesn’t include it, so the first build failed with an import error, and I added it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# Sets the working folder inside the container.
WORKDIR /code

# copies the list of Python packages and installs them 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# It copies the application code and the sample DEM into the image.
COPY app ./app
COPY data ./data

# starts the API with Uvicorn when the container runs
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
