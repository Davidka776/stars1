from flask import Flask, render_template, request, session, jsonify, redirect
from datetime import timedelta
import random
import sqlite3
import emoji
import logging
import os
import hashlib
import hmac
import json
from config import TASKS, REWARDS, TELEGRAM, REFERRAL
import requests
from utils import get_or_create_referral_code, get_referral_stats, process_referral_reward, add_referral

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = '2007david'

# Настройка сессий
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=5)
)

# Замените на ваш токен бота
BOT_TOKEN = '6003178703:AAE9UECUcRMBFybQa4BNMZps1e9zJQDK6o8'

def validate_telegram_data(init_data):
    try:
        # Разбираем строку init_data
        data_dict = dict(param.split('=') for param in init_data.split('&'))
        
        # Получаем hash
        received_hash = data_dict.pop('hash')
        
        # Сортируем оставшиеся параметры
        data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(data_dict.items()))
        
        # Создаем секретный ключ
        secret_key = hmac.new('WebAppData'.encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        return calculated_hash == received_hash
    except Exception as e:
        logger.error(f"Ошибка валидации данных Telegram: {e}")
        return False

def init_db():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id TEXT PRIMARY KEY,
                      username TEXT,
                      first_name TEXT,
                      verified INTEGER DEFAULT 0,
                      balance INTEGER DEFAULT 0)''')
                      
        c.execute('''CREATE TABLE IF NOT EXISTS completed_tasks
                     (user_id TEXT,
                      task_id INTEGER,
                      completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      PRIMARY KEY (user_id, task_id))''')
                      
        conn.commit()
        conn.close()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise e

def check_channel_subscription(user_id, channel):
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/getChatMember'
        params = {
            'chat_id': channel,
            'user_id': user_id
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                status = result['result']['status']
                # Проверяем все возможные статусы активного участника
                return status in ['member', 'administrator', 'creator']
        logger.warning(f"Неудачная проверка подписки: {response.json()}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return False

def add_balance(user_id, amount):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', 
                 (amount, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка при начислении баланса: {e}")
        return False

def is_task_completed(user_id, task_id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        result = c.execute('''SELECT 1 FROM completed_tasks 
                             WHERE user_id = ? AND task_id = ?''', 
                          (user_id, task_id)).fetchone()
        conn.close()
        return bool(result)
    except Exception as e:
        logger.error(f"Ошибка при проверке выполнения задания: {e}")
        return False

def mark_task_completed(user_id, task_id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''INSERT INTO completed_tasks (user_id, task_id) 
                     VALUES (?, ?)''', (user_id, task_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка при отметке задания как выполненного: {e}")
        return False

def verify_user_captcha(user_id, answer):
    """Проверяет ответ капчи пользователя"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT captcha FROM captcha_sessions WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result and str(result[0]) == str(answer):
        return True
    return False

@app.route('/')
def index():
    try:
        emojis = ['😊', '🌟', '🎮', '🎵', '🍕', '🐱', '🌺', '⚽', '❤️']
        correct_emoji = random.choice(emojis)
        wrong_emojis = random.sample([e for e in emojis if e != correct_emoji], 8)
        all_emojis = wrong_emojis + [correct_emoji]
        random.shuffle(all_emojis)
        
        session.clear()
        session['correct_emoji'] = correct_emoji
        logger.debug(f"Установлен correct_emoji в сессии: {correct_emoji}")
        
        return render_template('index.html', 
                             emojis=all_emojis, 
                             correct_emoji=correct_emoji)
    except Exception as e:
        logger.error(f"Ошибка в index: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/verify', methods=['POST'])
def verify():
    try:
        selected_emoji = request.form.get('emoji')
        correct_emoji = session.get('correct_emoji')
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        
        logger.debug(f"""
        Получены данные:
        selected_emoji: {selected_emoji}
        correct_emoji: {correct_emoji}
        user_id: {user_id}
        username: {username}
        first_name: {first_name}
        """)
        
        if not all([selected_emoji, correct_emoji, user_id]):
            missing = []
            if not selected_emoji: missing.append('emoji')
            if not correct_emoji: missing.append('correct_emoji')
            if not user_id: missing.append('user_id')
            error_msg = f'Отсутствуют данные: {", ".join(missing)}'
            logger.error(error_msg)
            return jsonify({'success': False, 'message': error_msg}), 400
        
        if selected_emoji == correct_emoji:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO users 
                     (user_id, username, first_name, verified) 
                     VALUES (?, ?, ?, 1)''', 
                     (user_id, username or '', first_name or ''))
            conn.commit()
            conn.close()
            
            logger.info(f"Пользователь {user_id} успешно верифицирован")
            return jsonify({
                'success': True,
                'message': 'Капча пройдена успешно!',
                'redirect': f'/tasks?user_id={user_id}'
            })
        
        logger.warning(f"Неверная капча для пользователя {user_id}")
        return jsonify({
            'success': False,
            'message': 'Неправильный выбор, попробуйте еще раз'
        })
        
    except Exception as e:
        logger.error(f"Ошибка в verify: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/tasks')
def tasks_page():
    try:
        # Получаем init_data из заголовка или query параметра
        init_data = request.args.get('tgWebAppData') or request.headers.get('X-Telegram-Web-App-Data')
        user_id = request.args.get('user_id')

        # Для разработки: если нет init_data и есть DEBUG режим, пропускаем проверку
        if app.debug and not init_data and user_id:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            user = c.execute('SELECT verified FROM users WHERE user_id = ?', (user_id,)).fetchone()
            conn.close()
            
            if not user or not user[0]:
                return redirect('/')
            
            # Получаем первое задание из конфига
            task = TASKS['channel_subscription']
            
            return render_template('tasks.html', 
                                 task=task,
                                 currency_name=REWARDS['currency_name'],
                                 user_id=user_id)
        
        # Для production: проверяем данные Telegram
        if not init_data or not validate_telegram_data(init_data):
            return jsonify({'error': 'Unauthorized'}), 401
            
        # Получаем user_id из валидированных данных
        data_dict = dict(param.split('=') for param in init_data.split('&'))
        user_data = json.loads(data_dict.get('user', '{}'))
        user_id = user_data.get('id')
        
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
            
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        user = c.execute('SELECT verified FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        
        if not user or not user[0]:
            return redirect('/')
        
        # Получаем первое задание из конфига
        task = TASKS['channel_subscription']
        
        return render_template('tasks.html', 
                             task=task,
                             currency_name=REWARDS['currency_name'],
                             user_id=user_id)
    except Exception as e:
        logger.error(f"Ошибка в tasks_page: {e}")
        return redirect('/')

@app.route('/check_subscription', methods=['POST'])
def check_subscription():
    try:
        user_id = request.form.get('user_id')
        task_id = request.form.get('task_id')
        test_mode = request.form.get('test_mode') == 'true'
        
        if not user_id or not task_id:
            return jsonify({
                'success': False,
                'message': 'Отсутствуют необходимые параметры'
            }), 400

        # Проверяем, не было ли задание уже выполнено
        if is_task_completed(user_id, task_id):
            return jsonify({
                'success': False,
                'message': 'Вы уже выполнили это задание'
            })

        task = TASKS['channel_subscription']
        channel = task['channel']
        reward = task['reward']

        # В тестовом режиме всегда считаем, что подписка есть
        is_subscribed = True if test_mode else check_channel_subscription(user_id, channel)

        if is_subscribed:
            # Начисляем награду
            if add_balance(user_id, reward):
                # Отмечаем задание как выполненное
                if mark_task_completed(user_id, task_id):
                    return jsonify({
                        'success': True,
                        'message': f'Поздравляем! Вы получили {reward} {REWARDS["currency_name"]}',
                        'reward': reward
                    })
                else:
                    # Откатываем начисление баланса, если не удалось отметить задание
                    add_balance(user_id, -reward)
                    return jsonify({
                        'success': False,
                        'message': 'Ошибка при сохранении прогресса'
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Ошибка при начислении награды'
                })
        else:
            return jsonify({
                'success': False,
                'message': f'Вы не подписаны на канал {channel}. Подпишитесь и попробуйте снова.'
            })

    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return jsonify({
            'success': False,
            'message': 'Произошла ошибка при проверке'
        }), 500

@app.route('/referral')
def referral():
    user_id = request.args.get('user_id')
    if not user_id:
        return "User ID is required", 400

    # Получаем или создаем реферальный код
    referral_code = get_or_create_referral_code(user_id)
    
    # Получаем статистику рефералов
    stats = get_referral_stats(user_id)
    
    return render_template('referral.html',
                         user_id=user_id,
                         referral_code=referral_code,
                         referrals=stats['referrals'],
                         total_referrals=stats['total_referrals'],
                         total_earnings=stats['total_earnings'],
                         currency_name=REWARDS['currency_name'],
                         referral_reward=REFERRAL['reward'],
                         bot_username=TELEGRAM['bot_username'])

@app.route('/wallet')
def wallet_page():
    try:
        # Получаем init_data из заголовка или query параметра
        init_data = request.args.get('tgWebAppData') or request.headers.get('X-Telegram-Web-App-Data')
        user_id = request.args.get('user_id')

        # Для разработки: если нет init_data и есть DEBUG режим, пропускаем проверку
        if app.debug and not init_data and user_id:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            
            # Получаем баланс пользователя
            user = c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()
            conn.close()
            
            if not user:
                return redirect('/')
            
            balance = user[0]
            
            return render_template('wallet.html', 
                                 user_id=user_id,
                                 balance=balance,
                                 currency_name=REWARDS['currency_name'])

        # Для production: проверяем данные Telegram
        if not init_data or not validate_telegram_data(init_data):
            return jsonify({'error': 'Unauthorized'}), 401
            
        # Получаем user_id из валидированных данных
        data_dict = dict(param.split('=') for param in init_data.split('&'))
        user_data = json.loads(data_dict.get('user', '{}'))
        user_id = user_data.get('id')
        
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
            
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        user = c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        
        if not user:
            return redirect('/')
        
        balance = user[0]
        
        return render_template('wallet.html', 
                             user_id=user_id,
                             balance=balance,
                             currency_name=REWARDS['currency_name'])
    except Exception as e:
        logger.error(f"Ошибка в wallet_page: {e}")
        return redirect('/')

@app.route('/fortune')
def fortune_page():
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect('/')
    return render_template('fortune.html', user_id=user_id)

@app.route('/exchange')
def exchange_page():
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect('/')
    return render_template('exchange.html', user_id=user_id)

@app.route('/verify_captcha', methods=['POST'])
def verify_captcha():
    user_id = request.form.get('user_id')
    captcha_answer = request.form.get('captcha')
    
    if not user_id or not captcha_answer:
        return jsonify({'success': False, 'message': 'Отсутствуют необходимые параметры'})

    # Проверяем капчу
    if verify_user_captcha(user_id, captcha_answer):
        # Отмечаем пользователя как верифицированного
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('UPDATE users SET verified = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        
        # Обрабатываем реферальную награду
        if process_referral_reward(user_id):
            print(f"Referral reward processed for user {user_id}")
        
        conn.close()
        return jsonify({
            'success': True,
            'message': 'Капча пройдена успешно!'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Неверный ответ, попробуйте еще раз'
        })

@app.route('/start')
def start():
    user_id = request.args.get('user_id')
    ref_code = request.args.get('ref')  # Получаем реферальный код
    
    if not user_id:
        return "User ID is required", 400
        
    # Если есть реферальный код, обрабатываем его
    if ref_code:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Находим реферера по коду
        c.execute('SELECT user_id FROM users WHERE referral_code = ?', (ref_code,))
        referrer = c.fetchone()
        
        if referrer:
            referrer_id = referrer[0]
            # Добавляем реферала (статус будет 'pending')
            add_referral(user_id, referrer_id)
        
        conn.close()
    
    # Перенаправляем на страницу с капчей
    return redirect(url_for('index', user_id=user_id))

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 