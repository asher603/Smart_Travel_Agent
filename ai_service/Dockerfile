FROM python:3.10-slim

WORKDIR /app

# 1. Install CPU version of PyTorch separately (prevents downloading large NVIDIA drivers)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2. Copy and install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy application code
COPY . ./ai_service

# 4. Set environment and run
ENV PYTHONPATH=/app
EXPOSE 8002

CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8002"]