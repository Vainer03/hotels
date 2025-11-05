const getApiBaseUrl = () => {
    return '/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

console.log(`API Base URL: ${API_BASE_URL}`);
console.log(`Current host: ${window.location.hostname}`);

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
                console.log(`🔧 Added user_id parameter: ${currentUser.id} for ${endpoint}`);
            }
        }

        try {
            console.log(`🌐 API Request: ${config.method || 'GET'} ${url}`);

            const response = await fetch(url, config);
            
            console.log(`📡 Response status: ${response.status} ${response.statusText}`);

            // Клонируем response для чтения тела
            const responseClone = response.clone();
            
            if (!response.ok) {
                let errorDetail = 'Unknown error';
                
                try {
                    // Читаем ответ как текст - ОСНОВНОЙ СПОСОБ
                    const responseText = await responseClone.text();
                    console.log(`❌ RAW RESPONSE BODY:`, responseText);
                    
                    if (responseText) {
                        // Пробуем распарсить как JSON
                        try {
                            const errorData = JSON.parse(responseText);
                            console.log(`❌ PARSED ERROR DATA:`, errorData);
                            
                            // Извлекаем информацию разными способами
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
                                errorDetail = JSON.stringify(errorData, null, 2);
                            }
                        } catch (jsonError) {
                            // Если не JSON, используем raw текст
                            errorDetail = responseText;
                        }
                    }
                } catch (textError) {
                    console.error(`❌ Could not read response:`, textError);
                    errorDetail = 'Could not read response body';
                }
                
                const errorMessage = `HTTP ${response.status}: ${errorDetail}`;
                console.error(`💥 COMPLETE ERROR INFO:`, {
                    url,
                    status: response.status,
                    headers: Object.fromEntries(response.headers.entries()),
                    body: errorDetail
                });
                
                throw new Error(errorMessage);
            }
            
            if (response.status === 204) {
                return { message: 'Deleted successfully' };
            }
            
            // Читаем успешный ответ
            const responseText = await response.text();
            if (!responseText) return {};
            
            try {
                return JSON.parse(responseText);
            } catch (parseError) {
                console.error(`❌ Success response parse error:`, parseError);
                throw new Error('Invalid JSON response');
            }
            
        } catch (error) {
            console.error(`💥 API Request Failed for ${url}:`, error);
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
        console.log(`💾 User saved to localStorage:`, user.email);
    }

    static getCurrentUser() {
        const userStr = localStorage.getItem(this.CURRENT_USER_KEY);
        const user = userStr ? JSON.parse(userStr) : null;
        console.log(`🔍 Current user from storage:`, user?.email || 'None');
        return user;
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
        const isAuth = !!this.getCurrentUser();
        console.log(`🔐 Authentication status:`, isAuth);
        return isAuth;
    }

    static logout() {
        console.log(`🚪 Logging out user`);
        localStorage.removeItem(this.CURRENT_USER_KEY);
        window.location.reload();
    }

    static async login(email, password) {
        try {
            console.log(`🔐 Login attempt for: ${email}`);
            
            // Пробуем загрузить пользователей через API с user_id параметром
            let users = [];
            try {
                console.log('🔄 Loading users from API with current user context...');
                
                // Получаем текущего пользователя (если есть) для передачи user_id
                const currentUser = this.getCurrentUser();
                const params = new URLSearchParams();
                
                if (currentUser) {
                    params.append('user_id', currentUser.id);
                    console.log(`🔧 Adding user_id parameter: ${currentUser.id}`);
                } else {
                    // Если нет текущего пользователя, пробуем без параметра или с дефолтным
                    console.log('ℹ️ No current user, trying without user_id parameter');
                }
                
                const queryString = params.toString();
                const endpoint = queryString ? `/users/?${queryString}` : '/users/';
                
                users = await ApiClient.get(endpoint);
                console.log(`✅ Successfully loaded ${users.length} users from API`);
                
            } catch (apiError) {
                console.error('❌ API loading failed:', apiError.message);
                // Fallback на фиксированных пользователей
                console.log('🔄 Using fixed users as fallback');
                users = this.getFixedUsers();
            }
            
            const user = users.find(u => u.email === email);
            
            if (user) {
                console.log(`✅ User authenticated:`, user.email);
                this.setCurrentUser(user);
                return user;
            } else {
                console.log(`❌ User not found with email: ${email}`);
                throw new Error(`Пользователь не найден. Доступные: ${users.map(u => u.email).join(', ')}`);
            }
            
        } catch (error) {
            console.error('💥 Login error:', error);
            throw error;
        }
    }


    static async register(userData) {
        try {
            console.log(`👤 Starting registration:`, userData);
            
            const registrationData = {
                ...userData,
                role: 'user'
            };
            
            console.log(`📤 Sending registration data:`, registrationData);
            
            const newUser = await ApiClient.post('/users/register', registrationData);
            console.log(`✅ Registration successful:`, newUser);
            
            this.setCurrentUser(newUser);
            return newUser;
        } catch (error) {
            console.error('💥 Registration failed:', {
                data: userData,
                error: error.message
            });
            throw error;
        }
    }

    static async loginWithDiagnosis(email, password) {
        try {
            console.group(`🔍 LOGIN DIAGNOSIS for ${email}`);
            
            // Сначала пробуем стандартный метод
            try {
                const user = await this.login(email, password);
                console.groupEnd();
                return user;
            } catch (loginError) {
                console.error(`❌ Standard login failed:`, loginError.message);
                
                // Если стандартный метод не работает, используем диагностику
                console.log(`🔄 Starting diagnostic mode...`);
                
                // Проверяем доступность разных эндпоинтов
                const endpointsToTest = [
                    '/users/',
                    '/users',
                    '/hotels/',
                    '/rooms/',
                    '/bookings/'
                ];
                
                const results = {};
                
                for (const endpoint of endpointsToTest) {
                    try {
                        const data = await ApiClient.get(endpoint);
                        results[endpoint] = { status: 'success', data: Array.isArray(data) ? `array[${data.length}]` : 'object' };
                    } catch (error) {
                        results[endpoint] = { status: 'error', message: error.message };
                    }
                }
                
                console.log(`📊 Endpoint availability:`, results);
                
                // Используем фиксированных пользователей если API недоступно
                console.log(`🔄 Using fixed users for diagnosis`);
                const fixedUsers = this.getFixedUsers();
                const user = fixedUsers.find(u => u.email === email);
                
                if (user) {
                    console.log(`✅ Fixed user found:`, user.email);
                    this.setCurrentUser(user);
                    console.groupEnd();
                    return user;
                } else {
                    console.log(`❌ User not found in fixed list`);
                    console.groupEnd();
                    throw new Error(`Пользователь не найден. Доступные emails: ${fixedUsers.map(u => u.email).join(', ')}`);
                }
            }
        } catch (error) {
            console.groupEnd();
            throw error;
        }
    }

    static getFixedUsers() {
        return [
            {
                id: 1,
                email: 'admin@hotels.com',
                first_name: 'Алексей',
                last_name: 'Администраторов',
                phone: '+79990000001',
                role: 'admin',
                created_at: new Date().toISOString()
            },
            {
                id: 2,
                email: 'manager@hotels.com', 
                first_name: 'Мария',
                last_name: 'Менеджерова',
                phone: '+79990000002',
                role: 'admin',
                created_at: new Date().toISOString()
            },
            {
                id: 3,
                email: 'ivan.petrov@example.com',
                first_name: 'Иван',
                last_name: 'Петров',
                phone: '+79991234567',
                role: 'user',
                created_at: new Date().toISOString()
            },
            {
                id: 4,
                email: 'maria.ivanova@example.com',
                first_name: 'Мария', 
                last_name: 'Иванова',
                phone: '+79992345678',
                role: 'user',
                created_at: new Date().toISOString()
            }
        ];
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

// Функция для тестирования всех эндпоинтов API
window.testApiEndpoints = async function() {
    console.group('🔧 API ENDPOINT TEST');
    
    const endpoints = [
        '/users/',
        '/users',
        '/hotels/',
        '/rooms/',
        '/bookings/'
    ];
    
    let results = [];
    
    for (const endpoint of endpoints) {
        try {
            console.log(`Testing ${endpoint}...`);
            const data = await ApiClient.get(endpoint);
            const result = {
                endpoint,
                status: '✅ SUCCESS',
                details: Array.isArray(data) ? `(${data.length} items)` : '(object)',
                data: data
            };
            console.log(`✅ ${endpoint}: SUCCESS`, result.details);
            results.push(result);
        } catch (error) {
            const result = {
                endpoint,
                status: '❌ ERROR',
                details: error.message,
                error: error
            };
            console.log(`❌ ${endpoint}: ERROR - ${error.message}`);
            results.push(result);
        }
    }
    
    console.log('📊 TEST RESULTS SUMMARY:', results);
    console.groupEnd();
    
    // Показываем результаты пользователю
    const successCount = results.filter(r => r.status === '✅ SUCCESS').length;
    const totalCount = results.length;
    
    UIUtils.showMessage(
        `Тест API завершен: ${successCount}/${totalCount} эндпоинтов работают. Смотрите консоль для деталей.`, 
        successCount === totalCount ? 'success' : 'error'
    );
    
    return results;
};

// Функция для детальной отладки ошибки API
window.debugApiError = async function() {
    console.group('🐛 API DEBUG MODE');
    
    try {
        console.log('🔍 Testing /api/v1/users/ endpoint...');
        
        const response = await fetch('/api/v1/users/');
        console.log('📡 Response details:', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok,
            headers: Object.fromEntries(response.headers.entries())
        });
        
        const text = await response.text();
        console.log('📄 Response text:', text);
        
        if (text) {
            try {
                const json = JSON.parse(text);
                console.log('🔍 Parsed JSON:', json);
                
                // Детальный анализ структуры ошибки
                if (Array.isArray(json)) {
                    console.log('📊 Error is an array, items:', json.length);
                    json.forEach((item, index) => {
                        console.log(`  [${index}]:`, item);
                    });
                } else if (typeof json === 'object') {
                    console.log('📊 Error is an object, keys:', Object.keys(json));
                    for (const [key, value] of Object.entries(json)) {
                        console.log(`  ${key}:`, value);
                    }
                }
            } catch (e) {
                console.log('❌ Not valid JSON:', e.message);
            }
        } else {
            console.log('❌ Empty response body');
        }
        
    } catch (error) {
        console.error('💥 Fetch failed:', error);
    }
    
    console.groupEnd();
    
    // Показываем уведомление пользователю
    alert('Debug completed! Check browser console for details.');
};

// Проверка что функции определены
console.log('🔧 utils.js loaded - debugApiError defined:', typeof debugApiError);
console.log('🔧 utils.js loaded - testApiEndpoints defined:', typeof testApiEndpoints);