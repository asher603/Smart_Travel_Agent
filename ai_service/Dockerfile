FROM python:3.10-slim

# 1. Setup the environment
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy code into a SUBDIRECTORY to preserve "ai_service" package name
COPY . ./ai_service

# 3. Add /app to PYTHONPATH so imports like "from ai_service..." work
ENV PYTHONPATH=/app

EXPOSE 8002

# 4. Run the module using the folder name
CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8002"]