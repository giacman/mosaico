# Mosaico Backend - Dockerfile for Cloud Run
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- DEBUG: List installed packages ---
RUN pip freeze > installed_packages.txt
# --- END DEBUG ---

# Copy application code
COPY ./app /app

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run application
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1

