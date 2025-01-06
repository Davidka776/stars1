// Тестовые данные пользователя для разработки
const testUser = {
    id: '12345678',
    username: 'test_user',
    first_name: 'Test User'
};

// Инициализация переменных
let tg;
let user;

try {
    if (window.Telegram && window.Telegram.WebApp) {
        tg = window.Telegram.WebApp;
        tg.expand();
        user = tg.initDataUnsafe.user || testUser;
        console.log('Запущено в Telegram:', user);
    } else {
        console.log('Запущено в браузере, используются тестовые данные');
        tg = {
            expand: () => {},
            MainButton: {
                show: () => {},
                hide: () => {}
            }
        };
        user = testUser;
    }
} catch (error) {
    console.log('Ошибка инициализации:', error);
    user = testUser;
    tg = {
        expand: () => {},
        MainButton: {
            show: () => {},
            hide: () => {}
        }
    };
}

// Добавим favicon для предотвращения 404 ошибки
const favicon = document.createElement('link');
favicon.rel = 'icon';
favicon.href = 'data:;base64,iVBORw0KGgo=';
document.head.appendChild(favicon);

function showMessage(message, isError = false) {
    if (isError) {
        console.error(message);
    }
    alert(message);
}

function verifyEmoji(selectedEmoji) {
    console.log('Верификация для пользователя:', user);

    fetch('/verify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `emoji=${encodeURIComponent(selectedEmoji)}&` +
              `user_id=${encodeURIComponent(user.id)}&` +
              `username=${encodeURIComponent(user.username || '')}&` +
              `first_name=${encodeURIComponent(user.first_name || '')}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showMessage(data.message);
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1000);
        } else {
            showMessage(data.message, true);
            setTimeout(() => {
                location.reload();
            }, 1000);
        }
    })
    .catch(error => {
        console.error('Error during verification:', error);
        showMessage('Произошла ошибка при проверке. Пожалуйста, попробуйте еще раз.', true);
        setTimeout(() => {
            location.reload();
        }, 1000);
    });
}

console.log('Текущий пользователь:', user); 