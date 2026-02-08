// ===========================
// 🔐 Модуль аутентификации
// ===========================

const AUTH_CONFIG = {
    API_BASE: 'http://localhost:8000/api',
    TOKEN_KEY: 'access_token',
    USERNAME_KEY: 'username',
    ROLE_KEY: 'user_role'
};

/**
 * Проверка авторизации пользователя
 */
function isAuthenticated() {
    const token = localStorage.getItem(AUTH_CONFIG.TOKEN_KEY);
    return token !== null && token !== '';
}

/**
 * Получение токена доступа
 */
function getAccessToken() {
    return localStorage.getItem(AUTH_CONFIG.TOKEN_KEY);
}

/**
 * Получение имени пользователя
 */
function getUsername() {
    return localStorage.getItem(AUTH_CONFIG.USERNAME_KEY);
}

/**
 * Получение роли пользователя
 */
function getUserRole() {
    return localStorage.getItem(AUTH_CONFIG.ROLE_KEY) || 'USER';
}

/**
 * Выход из системы
 */
function logout() {
    localStorage.removeItem(AUTH_CONFIG.TOKEN_KEY);
    localStorage.removeItem(AUTH_CONFIG.USERNAME_KEY);
    localStorage.removeItem(AUTH_CONFIG.ROLE_KEY);
    window.location.href = 'login.html';
}

/**
 * Защита страницы (редирект на login, если не авторизован)
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

/**
 * Добавление токена в запросы к API
 */
function getAuthHeaders() {
    const token = getAccessToken();
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

/**
 * Fetch с автоматической авторизацией
 */
async function authFetch(url, options = {}) {
    const defaultOptions = {
        headers: getAuthHeaders(),
        ...options
    };

    const response = await fetch(url, defaultOptions);

    // Если токен истек или невалиден - редирект на login
    if (response.status === 401) {
        logout();
        throw new Error('Unauthorized');
    }

    return response;
}

/**
 * Обновление UI с информацией о пользователе
 */
function updateUserInfo() {
    const username = getUsername();
    const userInfoElements = document.querySelectorAll('.user-info');

    userInfoElements.forEach(el => {
        if (username) {
            el.textContent = `👤 ${username}`;
        }
    });
}

/**
 * Добавление кнопки выхода
 */
function addLogoutButton() {
    const logoutBtn = document.createElement('button');
    logoutBtn.textContent = '🚪 Logout';
    logoutBtn.className = 'logout-btn';
    logoutBtn.onclick = logout;

    // Добавляем в header-right, если он есть
    const headerRight = document.querySelector('.header-right');
    if (headerRight && isAuthenticated()) {
        headerRight.appendChild(logoutBtn);
    }
}

// Экспорт функций
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        isAuthenticated,
        getAccessToken,
        getUsername,
        getUserRole,
        logout,
        requireAuth,
        getAuthHeaders,
        authFetch,
        updateUserInfo,
        addLogoutButton,
        AUTH_CONFIG
    };
}