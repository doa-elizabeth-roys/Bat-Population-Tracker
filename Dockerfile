FROM python:3.10-slim

# System dependencies for OpenCV and Google Cloud
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# Expose port for Fly.io
EXPOSE 8080

# Run the app
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8080", "--workers=1"]
