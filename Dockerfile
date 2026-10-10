FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bank ./bank
COPY sql ./sql
EXPOSE 8000
