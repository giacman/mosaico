# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the entire backend directory into the container.
# This includes alembic.ini, migrations/, app/, etc.
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# The command to run when the container starts (passed to the entrypoint)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]

