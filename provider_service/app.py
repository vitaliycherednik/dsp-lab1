import logging
import time
import jwt
from flask import Flask, request, jsonify
import os

# Налаштування логування
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Секретний ключ для перевірки JWT (має бути таким самим, як у consumer service)
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')

def verify_token(auth_header):
    """
    Перевіряє JWT токен з заголовка Authorization
    """
    if not auth_header:
        raise jwt.InvalidTokenError("Missing authorization header")

    try:
        token = auth_header.split(' ')[1]
        # Перевіряємо токен та його термін дії
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        # Перевіряємо, чи це токен від consumer service
        if payload.get('service') != 'consumer':
            raise jwt.InvalidTokenError("Invalid service token")

        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(str(e))
    except Exception as e:
        raise jwt.InvalidTokenError(f"Token verification failed: {str(e)}")

@app.route('/compute', methods=['POST'])
def compute():
    start_time = time.time()

    try:
        # Перевіряємо токен
        try:
            verify_token(request.headers.get('Authorization'))
        except jwt.InvalidTokenError as e:
            logger.error(f'Authorization failed: {str(e)}')
            return jsonify({'error': str(e)}), 401

        # Отримуємо дані для обчислення
        data = request.get_json()

        if not data:
            logger.error('Empty request data')
            return jsonify({'error': 'Empty request'}), 400

        num1 = data.get('num1')
        num2 = data.get('num2')

        if num1 is None or num2 is None:
            logger.error('Missing parameters in request')
            return jsonify({'error': 'Missing parameters'}), 400

        # Виконуємо обчислення
        result = num1 + num2

        end_time = time.time()
        computation_duration = end_time - start_time

        # Логуємо час обчислення
        logger.info(f'Computation duration: {computation_duration:.4f} seconds')
        logger.info(f'Computed result: {result}')

        return jsonify({
            'result': result,
            'computation_time': computation_duration
        }), 200

    except Exception as e:
        logger.exception(f'Error processing request: {str(e)}')
        return jsonify({'error': 'Computation failed', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
