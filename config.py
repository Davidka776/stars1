# Конфигурация заданий
TASKS = {
    'channel_subscription': {
        'id': 1,
        'type': 'channel_subscription',
        'title': 'Подписка на канал',
        'description': 'Подпишитесь на наш канал и получите награду',
        'channel': '@FreePremGift',  # Замените на ваш канал
        'reward': 100,  # Награда в монетах
        'status': 'active',  # active/inactive
        'required_time': 24  # Время в часах, которое нужно оставаться подписанным
    }
}

# Конфигурация наград
REWARDS = {
    'currency_name': 'монет',
    'min_withdrawal': 1000,  # Минимальная сумма для вывода
}

# Конфигурация Telegram
TELEGRAM = {
    'bot_username': 'IZIGC_bot',  # Замените на username вашего бота
    'bot_token': '6003178703:AAE9UECUcRMBFybQa4BNMZps1e9zJQDK6o8'  # Замените на токен вашего бота
}

# Конфигурация реферальной системы
REFERRAL = {
    'reward': 100,  # Награда за каждого реферала
    'min_reward_balance': 10,  # Минимальный баланс реферала для получения награды
    'code_length': 8  # Длина реферального кода
} 