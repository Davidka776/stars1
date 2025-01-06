// Глобальные переменные
const tg = window.Telegram.WebApp;
const testUser = {
    id: '12345678', // Будет обновлено после загрузки DOM
    username: 'test_user',
    first_name: 'Test User',
    isSubscribed: false
};

// Функция для навигации
function navigateTo(section) {
    // Получаем текущий user_id из URL или meta тега
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('user_id') || document.querySelector('meta[name="user_id"]')?.content;
    
    // Получаем текущий путь
    const currentPath = window.location.pathname.substring(1); // убираем начальный слэш
    
    // Если мы уже на нужной странице, не делаем редирект
    if (currentPath === section) {
        return;
    }
    
    // В зависимости от выбранного раздела выполняем соответствующие действия
    switch(section) {
        case 'tasks':
            window.location.href = `/tasks?user_id=${userId}`;
            break;
        case 'referral':
            window.location.href = `/referral?user_id=${userId}`;
            break;
        case 'wallet':
            window.location.href = `/wallet?user_id=${userId}`;
            break;
        case 'fortune':
            window.location.href = `/fortune?user_id=${userId}`;
            break;
        case 'exchange':
            window.location.href = `/exchange?user_id=${userId}`;
            break;
    }
}

// Делаем функцию навигации глобальной
window.navigateTo = navigateTo;

// Функция для показа уведомлений
function showNotification(message, type = 'success') {
    // Удаляем существующие уведомления
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Создаем новое уведомление
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Выбираем иконку в зависимости от типа
    let icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    notification.innerHTML = `
        <span class="notification-icon">${icon}</span>
        <span class="notification-message">${message}</span>
    `;

    document.body.appendChild(notification);

    // Показываем уведомление
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);

    // Скрываем и удаляем уведомление
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Обновляем функции показа сообщений
function showSuccessMessage(message) {
    if (tg.platform === 'unknown') {
        showNotification(message, 'success');
    } else {
        tg.showPopup({
            title: 'Успех!',
            message: message,
            buttons: [{type: 'ok'}]
        });
    }
}

function showErrorMessage(message) {
    if (tg.platform === 'unknown') {
        showNotification(message, 'error');
    } else {
        tg.showPopup({
            title: 'Ошибка',
            message: message,
            buttons: [{type: 'ok'}]
        });
    }
}

// Функции
function subscribeToChannel(channelUsername) {
    if (tg.platform === 'unknown') {
        // Предотвращаем повторное нажатие
        const subscribeButton = document.querySelector('.subscribe-button');
        if (subscribeButton.disabled) return;
        
        subscribeButton.disabled = true;
        testUser.isSubscribed = true;
        showSuccessMessage('Вы успешно подписались на канал (тестовый режим)');
        
        setTimeout(() => {
            subscribeButton.disabled = false;
        }, 1000);
    } else {
        window.open(`https://t.me/${channelUsername.replace('@', '')}`, '_blank');
    }
}

function checkSubscription() {
    // Предотвращаем повторное нажатие
    const checkButton = document.querySelector('.check-button');
    if (checkButton.disabled) return;
    
    const user = tg.initDataUnsafe.user || testUser;
    const userId = user.id;
    
    const originalText = checkButton.textContent;
    checkButton.textContent = 'Проверяем...';
    checkButton.disabled = true;

    if (tg.platform === 'unknown') {
        setTimeout(() => {
            if (testUser.isSubscribed) {
                fetch('/check_subscription', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `user_id=${encodeURIComponent(userId)}&task_id=1&test_mode=true`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showSuccessMessage(data.message);
                        const balanceElement = document.querySelector('.balance-amount');
                        if (balanceElement && data.reward) {
                            const currentBalance = parseInt(balanceElement.textContent);
                            balanceElement.textContent = `${currentBalance + data.reward}`;
                        }
                    } else {
                        showErrorMessage(data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showErrorMessage('Произошла ошибка при проверке подписки');
                })
                .finally(() => {
                    checkButton.textContent = originalText;
                    checkButton.disabled = false;
                });
            } else {
                showErrorMessage('Вы не подписаны на канал. Нажмите кнопку "Подписаться" сначала.');
                checkButton.textContent = originalText;
                checkButton.disabled = false;
            }
        }, 1000);
    } else {
        // Реальная проверка для Telegram
        fetch('/check_subscription', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `user_id=${encodeURIComponent(userId)}&task_id=1`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccessMessage(data.message);
                const balanceElement = document.querySelector('.balance-amount');
                if (balanceElement && data.reward) {
                    const currentBalance = parseInt(balanceElement.textContent);
                    balanceElement.textContent = `${currentBalance + data.reward}`;
                }
            } else {
                showErrorMessage(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('Произошла ошибка при проверке подписки');
        })
        .finally(() => {
            checkButton.textContent = originalText;
            checkButton.disabled = false;
        });
    }
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    // Обновляем ID тестового пользователя из meta-тега
    const userIdMeta = document.querySelector('meta[name="user_id"]');
    if (userIdMeta) {
        testUser.id = userIdMeta.content;
    }

    // Расширяем WebApp
    tg.expand();

    // Добавляем обработчики событий для кнопок
    document.querySelector('.subscribe-button').addEventListener('click', function() {
        subscribeToChannel(this.dataset.channel);
    });
    
    document.querySelector('.check-button').addEventListener('click', function() {
        checkSubscription();
    });

    // Обработка темы
    function updateTheme() {
        document.body.setAttribute('data-theme', tg.colorScheme);
    }

    tg.onEvent('themeChanged', updateTheme);
    updateTheme();
}); 