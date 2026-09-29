FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bank ./bank
COPY app.py ./app.py
COPY .streamlit ./.streamlit
EXPOSE 8000 8501
