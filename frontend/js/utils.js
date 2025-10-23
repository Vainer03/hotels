const getApiBaseUrl = () => {
    return '/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

console.log(`API Base URL: ${API_BASE_URL}`);
console.log(`Current host: ${window.location.hostname}`);
class ApiClient {
    static async get(endpoint) {
        try {
            console.log(`GET ${endpoint}`);
            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`GET ${endpoint} response:`, data);
            return data;
        } catch (error) {
            console.error(`GET Error ${endpoint}:`, error);
            throw error;
        }
    }

    static async post(endpoint, data) {
        try {
            console.log(`POST ${endpoint}:`, data);
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const responseData = await response.json();
            
            if (!response.ok) {
                throw new Error(responseData.detail || `HTTP error! status: ${response.status}`);
            }
            
            console.log(`POST ${endpoint} response:`, responseData);
            return responseData;
        } catch (error) {
            console.error(`POST Error ${endpoint}:`, error);
            throw error;
        }
    }

    static async put(endpoint, data) {
        try {
            console.log(`PUT ${endpoint}:`, data);
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const responseData = await response.json();
            
            if (!response.ok) {
                throw new Error(responseData.detail || `HTTP error! status: ${response.status}`);
            }
            
            console.log(`PUT ${endpoint} response:`, responseData);
            return responseData;
        } catch (error) {
            console.error(`PUT Error ${endpoint}:`, error);
            throw error;
        }
    }

    static async delete(endpoint) {
        try {
            console.log(`DELETE ${endpoint}`);
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'DELETE'
            });
            
            if (response.status === 204) { // No Content
                return { message: 'Deleted successfully' };
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }
            
            console.log(`DELETE ${endpoint} response:`, data);
            return data;
        } catch (error) {
            console.error(`DELETE Error ${endpoint}:`, error);
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