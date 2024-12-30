import os
import requests
import logging
import time
import jwt  # Бібліотека для роботи з JWT
from flask import Flask, jsonify, request
import datetime

# Налаштування логування
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Отримуємо URL провайдера з змінної середовища
PROVIDER_URL = os.getenv('PROVIDER_URL', 'http://provider_balancer:80/compute')

# Секретний ключ для підпису JWT
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')

@app.route('/token', methods=['POST'])
def generate_user_token():
    """
    Генерує JWT токен для клієнта.
    """
    try:
        # Отримуємо дані користувача (наприклад, ім'я або роль)
        user_data = request.get_json()
        username = user_data.get("username", "anonymous")
        role = user_data.get("role", "user")

        # Генеруємо токен з певними даними
        payload = {
            "username": username,
            "role": role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Час дії токена - 1 година
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify({"token": token}), 200
    except Exception as e:
        return jsonify({"error": f"Could not generate token: {str(e)}"}), 500

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Перевіряємо наявність токену в заголовках
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401

        try:
            # Отримуємо токен з заголовка Authorization: Bearer <token>
            token = auth_header.split(' ')[1]
            # Перевіряємо токен
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        # Отримуємо дані з запиту або використовуємо значення за замовчуванням
        data = request.get_json() if request.is_json else {'num1': 10, 'num2': 20}

        start_time = time.time()

        # Створюємо новий токен для provider service
        provider_payload = {
            "service": "consumer",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        }
        provider_token = jwt.encode(provider_payload, SECRET_KEY, algorithm="HS256")

        # Надсилання запиту до Provider Service через балансувальник
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {provider_token}'
        }
        response = requests.post(PROVIDER_URL, json=data, headers=headers)

        end_time = time.time()
        request_duration = end_time - start_time

        # Логування часу виконання запиту
        logger.info(f'Request duration: {request_duration:.4f} seconds')

        if response.status_code == 200:
            result = response.json()
            result['consumer_processing_time'] = request_duration
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Computation failed'}), 500

    except requests.RequestException as e:
        logger.error(f'Request error: {e}')
        return jsonify({'error': 'Service unavailable'}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
