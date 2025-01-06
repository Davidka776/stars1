// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

// Функция для навигации по разделам
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

// Функция для показа всплывающего окна
function showPopup(title, message) {
    if (tg.platform === 'unknown') {
        // Если открыто не в Telegram, показываем обычный alert
        alert(`${title}\n${message}`);
    } else {
        // Если открыто в Telegram, используем нативный popup
        tg.showPopup({
            title: title,
            message: message,
            buttons: [{
                type: 'ok'
            }]
        });
    }
}

// Обработка темной/светлой темы
function updateTheme() {
    document.body.setAttribute('data-theme', tg.colorScheme);
}

// Слушаем изменения темы
tg.onEvent('themeChanged', updateTheme);
updateTheme(); 