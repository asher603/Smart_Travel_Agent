FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy into subdirectory
COPY . ./server

# Allow imports from root
ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8001"]