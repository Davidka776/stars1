// Глобальные переменные
const tg = window.Telegram.WebApp;
const testUser = {
    id: '12345678',
    username: 'test_user',
    first_name: 'Test User'
};

// Функция для навигации
function navigateTo(section) {
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('user_id') || document.querySelector('meta[name="user_id"]')?.content;
    
    const currentPath = window.location.pathname.substring(1);
    if (currentPath === section) {
        return;
    }
    
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

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    // Обновляем ID тестового пользователя из meta-тега
    const userIdMeta = document.querySelector('meta[name="user_id"]');
    if (userIdMeta) {
        testUser.id = userIdMeta.content;
    }

    // Расширяем WebApp
    tg.expand();

    // Обработка темы
    function updateTheme() {
        document.body.setAttribute('data-theme', tg.colorScheme);
    }

    tg.onEvent('themeChanged', updateTheme);
    updateTheme();
});

// Функция копирования реферальной ссылки
function copyReferralLink() {
    const linkInput = document.querySelector('.link-input');
    linkInput.select();
    
    try {
        // Пытаемся скопировать текст
        document.execCommand('copy');
        
        // Показываем уведомление
        showNotification('Ссылка скопирована!', 'success');
        
        // Снимаем выделение
        window.getSelection().removeAllRanges();
    } catch (err) {
        showNotification('Не удалось скопировать ссылку', 'error');
    }
}

// Функция для показа уведомлений (такая же, как в tasks.js)
function showNotification(message, type = 'success') {
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    let icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    notification.innerHTML = `
        <span class="notification-icon">${icon}</span>
        <span class="notification-message">${message}</span>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('show');
    }, 100);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Делаем функцию копирования глобальной
window.copyReferralLink = copyReferralLink; 