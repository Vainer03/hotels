const getApiBaseUrl = () => {
    return '/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

class ApiClient {
    static async request(endpoint, options = {}) {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        let url = `${API_BASE_URL}${endpoint}`;
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem(this.CURRENT_USER_KEY);
                    throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
                }
                
                let errorDetail = '';
                
                try {
                    const responseText = await response.text();
                    if (responseText) {
                        try {
                            const errorData = JSON.parse(responseText);
                            if (errorData.detail) {
                                errorDetail = String(errorData.detail);
                            } else {
                                errorDetail = JSON.stringify(errorData);
                            }
                        } catch {
                            errorDetail = responseText;
                        }
                    }
                } catch {
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
            const response = await fetch(`${API_BASE_URL}/users/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка при входе в систему');
            }
            
            const tokenData = await response.json();
            const user = tokenData.user;
            
            localStorage.setItem('access_token', tokenData.access_token);
            this.setCurrentUser(user);
            
            return user;
        } catch (error) {
            throw new Error('Ошибка при входе в систему: ' + error.message);
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
            throw error;
        }
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