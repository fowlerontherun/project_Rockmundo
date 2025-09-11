FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .
COPY backend/scripts/docker-entrypoint.sh /app/

# Expose the port the app runs on
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
# Run the application
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
