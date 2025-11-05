const getApiBaseUrl = () => {
    return '/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

console.log(`API Base URL: ${API_BASE_URL}`);

class ApiClient {
    static async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        const config = {
            ...options,
            headers
        };

        let url = `${API_BASE_URL}${endpoint}`;
        
        // Добавляем user_id для всех запросов, которые его требуют
        const currentUser = AuthManager.getCurrentUser();
        if (currentUser) {
            // Определяем эндпоинты, которые требуют user_id
            const endpointsRequiringUserId = ['/users/', '/users', '/bookings/', '/bookings'];
            const requiresUserId = endpointsRequiringUserId.some(ep => endpoint.includes(ep));
            
            if (requiresUserId) {
                const separator = url.includes('?') ? '&' : '?';
                url += `${separator}user_id=${currentUser.id}`;
            }
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                let errorDetail = '';
                
                try {
                    const responseText = await response.text();
                    
                    if (responseText) {
                        try {
                            const errorData = JSON.parse(responseText);
                            
                            if (Array.isArray(errorData)) {
                                errorDetail = errorData.map(err => {
                                    if (err.loc && err.msg) {
                                        return `${err.loc.join('.')}: ${err.msg}`;
                                    }
                                    return JSON.stringify(err);
                                }).join('; ');
                            } else if (errorData.detail) {
                                if (Array.isArray(errorData.detail)) {
                                    errorDetail = errorData.detail.map(d => 
                                        `${d.loc?.join('.') || 'field'}: ${d.msg || JSON.stringify(d)}`
                                    ).join('; ');
                                } else {
                                    errorDetail = String(errorData.detail);
                                }
                            } else {
                                errorDetail = JSON.stringify(errorData);
                            }
                        } catch (jsonError) {
                            errorDetail = responseText;
                        }
                    }
                } catch (textError) {
                    errorDetail = 'Could not read response body';
                }
                
                throw new Error(`HTTP ${response.status}: ${errorDetail}`);
            }
            
            if (response.status === 204) {
                return { message: 'Deleted successfully' };
            }
            
            const responseText = await response.text();
            if (!responseText) return {};
            
            return JSON.parse(responseText);
            
        } catch (error) {
            console.error(`API Request Failed for ${url}:`, error);
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

class AuthManager {
    static CURRENT_USER_KEY = 'current_user';

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
        window.location.reload();
    }

    static async login(email, password) {
        try {
            // Загружаем пользователей через API
            const users = await ApiClient.get('/users/');
            const user = users.find(u => u.email === email);
            
            if (user) {
                this.setCurrentUser(user);
                return user;
            } else {
                throw new Error('Пользователь с таким email не найден');
            }
            
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    static async register(userData) {
        try {
            const registrationData = {
                ...userData,
                role: 'user'
            };
            
            const newUser = await ApiClient.post('/users/register', registrationData);
            this.setCurrentUser(newUser);
            return newUser;
        } catch (error) {
            console.error('Registration error:', error);
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