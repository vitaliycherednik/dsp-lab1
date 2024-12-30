FROM python:3.9-slim

WORKDIR /app

COPY consumer_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY consumer_service/app.py .

CMD ["python", "app.py"]
