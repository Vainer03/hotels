const getApiBaseUrl = () => {
    return '/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

console.log(`API Base URL: ${API_BASE_URL}`);
console.log(`Current host: ${window.location.hostname}`);

class AuthManager {
    static CURRENT_USER_KEY = 'current_user';
    static TOKEN_KEY = 'auth_token';

    static setCurrentUser(user) {
        localStorage.setItem(this.CURRENT_USER_KEY, JSON.stringify(user));
    }

    static getCurrentUser() {
        const userStr = localStorage.getItem(this.CURRENT_USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    }

    static isAdmin() {
        const user = this.getCurrentUser();
        return user && user.role === 'admin';
    }

    static isUser() {
        const user = this.getCurrentUser();
        return user && user.role === 'user';
    }

    static isAuthenticated() {
        return !!this.getCurrentUser();
    }

    static logout() {
        localStorage.removeItem(this.CURRENT_USER_KEY);
        localStorage.removeItem(this.TOKEN_KEY);
        window.location.reload();
    }

    static async login(email, password) {
        // Временная реализация - в реальном приложении здесь будет JWT
        try {
            const users = await ApiClient.get('/users/');
            const user = users.find(u => u.email === email);
            
            if (user) {
                this.setCurrentUser(user);
                return user;
            } else {
                throw new Error('Пользователь не найден');
            }
        } catch (error) {
            throw new Error('Ошибка авторизации');
        }
    }

    static async register(userData) {
        try {
            const newUser = await ApiClient.post('/users/register', userData);
            this.setCurrentUser(newUser);
            return newUser;
        } catch (error) {
            throw error;
        }
    }
}

class ApiClient {
    static async request(endpoint, options = {}) {
        const user = AuthManager.getCurrentUser();
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        // Добавляем user_id в заголовки для временной аутентификации
        if (user) {
            headers['X-User-ID'] = user.id;
        }

        const config = {
            ...options,
            headers
        };

        try {
            console.log(`${config.method || 'GET'} ${endpoint}`);
            const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
            
            if (response.status === 403) {
                UIUtils.showMessage('Доступ запрещен. Недостаточно прав.', 'error');
                throw new Error('Доступ запрещен');
            }
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            
            // Для DELETE запросов может не быть тела
            if (response.status === 204) {
                return { message: 'Deleted successfully' };
            }
            
            const data = await response.json();
            console.log(`${config.method || 'GET'} ${endpoint} response:`, data);
            return data;
        } catch (error) {
            console.error(`API Error ${endpoint}:`, error);
            throw error;
        }
    }

    static async get(endpoint) {
        return this.request(endpoint);
    }

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

class UIUtils {
    static showMessage(message, type = 'success') {
        const messageEl = document.getElementById('message');
        messageEl.textContent = message;
        messageEl.className = `message ${type}`;
        messageEl.classList.remove('hidden');
        
        setTimeout(() => {
            messageEl.classList.add('hidden');
        }, 5000);
    }

    static formatDate(dateString) {
        if (!dateString) return 'Не указано';
        try {
            return new Date(dateString).toLocaleDateString('ru-RU');
        } catch {
            return dateString;
        }
    }

    static formatDateTime(dateString) {
        if (!dateString) return 'Не указано';
        try {
            return new Date(dateString).toLocaleString('ru-RU');
        } catch {
            return dateString;
        }
    }

    static getRoomStatusClass(status) {
        const statusMap = {
            'available': 'status-available',
            'occupied': 'status-occupied',
            'maintenance': 'status-maintenance',
            'cleaning': 'status-cleaning'
        };
        return statusMap[status] || 'status-unknown';
    }
}

class FormUtils {
    static getFormData(formId) {
        const form = document.getElementById(formId);
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (key === 'floor' || key === 'capacity' || key === 'hotel_id' || key === 'user_id' || 
                key === 'room_id' || key === 'number_of_guests') {
                data[key] = value ? parseInt(value) : null;
            } else if (key === 'price_per_night' || key === 'rating' || key === 'total_price') {
                data[key] = value ? parseFloat(value) : null;
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }

    static setFormData(formId, data) {
        const form = document.getElementById(formId);
        for (const [key, value] of Object.entries(data)) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = value || '';
            }
        }
    }

    static clearForm(formId) {
        const form = document.getElementById(formId);
        form.reset();
    }
}