# Dockerfile

FROM python:3.10

WORKDIR /app
COPY . .

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
