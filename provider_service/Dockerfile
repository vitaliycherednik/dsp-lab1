FROM python:3.9-slim

WORKDIR /app

COPY provider_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY provider_service/app.py .

CMD ["python", "app.py"]
