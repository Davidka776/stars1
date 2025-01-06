import random
import string
import sqlite3
from config import REFERRAL

def generate_referral_code(length=REFERRAL['code_length']):
    """Генерирует уникальный реферальный код"""
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        # Проверяем, не существует ли уже такой код
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM users WHERE referral_code = ?', (code,))
        if c.fetchone()[0] == 0:
            conn.close()
            return code
        conn.close()

def get_or_create_referral_code(user_id):
    """Получает существующий или создает новый реферальный код для пользователя"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Проверяем, есть ли уже код
    c.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    
    if result and result[0]:
        code = result[0]
    else:
        # Создаем новый код
        code = generate_referral_code()
        c.execute('UPDATE users SET referral_code = ? WHERE user_id = ?', (code, user_id))
        conn.commit()
    
    conn.close()
    return code

def get_referral_stats(user_id):
    """Получает статистику рефералов пользователя"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Получаем список рефералов
    c.execute('''
        SELECT u.first_name, r.joined_at, r.reward 
        FROM referrals r 
        JOIN users u ON r.referral_id = u.user_id 
        WHERE r.referrer_id = ? 
        ORDER BY r.joined_at DESC
    ''', (user_id,))
    referrals = [{
        'first_name': row[0] or 'Пользователь',
        'date': row[1].split()[0] if row[1] else 'Неизвестно',
        'reward': row[2]
    } for row in c.fetchall()]
    
    # Получаем общую статистику
    c.execute('''
        SELECT COUNT(*), SUM(reward) 
        FROM referrals 
        WHERE referrer_id = ?
    ''', (user_id,))
    total_count, total_earnings = c.fetchone()
    
    conn.close()
    
    return {
        'referrals': referrals,
        'total_referrals': total_count or 0,
        'total_earnings': total_earnings or 0
    } 

def process_referral_reward(referral_id):
    """
    Начисляет награду рефереру после прохождения капчи рефералом
    """
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Проверяем, есть ли реферал в таблице referrals
        c.execute('''
            SELECT referrer_id, reward 
            FROM referrals 
            WHERE referral_id = ? AND status = 'pending'
        ''', (referral_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return False
            
        referrer_id, existing_reward = result
        
        # Если награда уже была начислена, пропускаем
        if existing_reward > 0:
            conn.close()
            return False
            
        # Начисляем награду рефереру
        reward = REFERRAL['reward']
        c.execute('''
            UPDATE users 
            SET balance = balance + ? 
            WHERE user_id = ?
        ''', (reward, referrer_id))
        
        # Обновляем статус и награду в таблице referrals
        c.execute('''
            UPDATE referrals 
            SET status = 'completed', reward = ? 
            WHERE referral_id = ?
        ''', (reward, referral_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error processing referral reward: {e}")
        if conn:
            conn.close()
        return False

def add_referral(referral_id, referrer_id):
    """
    Добавляет нового реферала в систему
    """
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Проверяем, не является ли пользователь уже чьим-то рефералом
        c.execute('SELECT referrer_id FROM referrals WHERE referral_id = ?', (referral_id,))
        if c.fetchone():
            conn.close()
            return False
            
        # Добавляем запись о реферале со статусом 'pending'
        c.execute('''
            INSERT INTO referrals (referral_id, referrer_id, status, reward)
            VALUES (?, ?, 'pending', 0)
        ''', (referral_id, referrer_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error adding referral: {e}")
        if conn:
            conn.close()
        return False 