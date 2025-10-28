class HotelBookingApp {
    constructor() {
        this.currentTab = 'hotels';
        this.hotels = [];
        this.rooms = [];
        this.bookings = [];
        this.users = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.showTab('hotels');
    }

    setupEventListeners() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const tab = e.target.getAttribute('data-tab');
                this.showTab(tab);
            });
        });
    }

    async loadInitialData() {
        console.log('🚀 Starting initial data load...');
        
        try {
            await Promise.all([
                this.loadHotels(),
                this.loadRooms(),
                this.loadBookings(),
                this.loadUsers()
            ]);
            console.log('✅ All data loaded successfully');
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
            UIUtils.showMessage('Ошибка загрузки данных. Проверьте, запущен ли бэкенд на localhost:8000', 'error');
        }
    }

    async loadHotels() {
        try {
            console.log('🏨 Loading hotels...');
            this.hotels = await ApiClient.get('/hotels/');
            console.log(`✅ Loaded ${this.hotels.length} hotels`);
            this.renderHotels();
        } catch (error) {
            console.error('❌ Error loading hotels:', error);
            throw error;
        }
    }

    async loadRooms() {
        try {
            console.log('🛏️ Loading rooms...');
            this.rooms = await ApiClient.get('/rooms/');
            console.log(`✅ Loaded ${this.rooms.length} rooms`);
            this.renderRooms();
        } catch (error) {
            console.error('❌ Error loading rooms:', error);
            throw error;
        }
    }

    async loadBookings() {
        try {
            console.log('📅 Loading bookings...');
            this.bookings = await ApiClient.get('/bookings/');
            console.log(`✅ Loaded ${this.bookings.length} bookings`);
            this.renderBookings();
        } catch (error) {
            console.error('❌ Error loading bookings:', error);
            throw error;
        }
    }

    async loadUsers() {
        try {
            console.log('👥 Loading users...');
            this.users = await ApiClient.get('/users/');
            console.log(`✅ Loaded ${this.users.length} users`);
            this.renderGuests();
        } catch (error) {
            console.error('❌ Error loading users:', error);
            throw error;
        }
    }

    showTab(tabName) {
        // Скрыть все табы
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Убрать активный класс со всех кнопок
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Показать выбранный таб
        document.getElementById(`${tabName}-tab`).classList.add('active');
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        this.currentTab = tabName;
        
        // Обновить данные если нужно
        if (tabName === 'guests') {
            this.renderGuests();
        }
    }

    renderHotels() {
        const container = document.getElementById('hotels-list');
        if (!container) return;
        
        if (!this.hotels.length) {
            container.innerHTML = '<p>🏨 Отели не найдены. Добавьте первый отель!</p>';
            return;
        }

        container.innerHTML = this.hotels.map(hotel => `
            <div class="card">
                <h3>${hotel.name}</h3>
                <p><strong>📍 Адрес:</strong> ${hotel.address}</p>
                <p><strong>🏙️ Город:</strong> ${hotel.city}, ${hotel.country}</p>
                <p><strong>⭐ Рейтинг:</strong> ${hotel.rating || 'Нет оценки'}</p>
                ${hotel.description ? `<p><strong>📝 Описание:</strong> ${hotel.description}</p>` : ''}
                <p><strong>📅 Создан:</strong> ${UIUtils.formatDate(hotel.created_at)}</p>
                
                <div class="card-actions">
                    <button class="btn btn-warning" onclick="app.editHotel(${hotel.id})">✏️ Редактировать</button>
                    <button class="btn btn-danger" onclick="app.deleteHotel(${hotel.id})">🗑️ Удалить</button>
                </div>
            </div>
        `).join('');
    }

    renderRooms() {
        const container = document.getElementById('rooms-list');
        if (!container) return;
        
        if (!this.rooms.length) {
            container.innerHTML = '<p>🛏️ Комнаты не найдены. Добавьте первую комнату!</p>';
            return;
        }

        container.innerHTML = this.rooms.map(room => {
            const hotel = this.hotels.find(h => h.id === room.hotel_id);
            const statusClass = UIUtils.getRoomStatusClass(room.status);
            const statusText = this.getRoomStatusText(room.status);
            
            return `
                <div class="card">
                    <h3>🛏️ Комната ${room.room_number}</h3>
                    <p><strong>🏨 Отель:</strong> ${hotel?.name || 'Неизвестно'}</p>
                    <p><strong>🏢 Этаж:</strong> ${room.floor}</p>
                    <p><strong>📋 Тип:</strong> ${room.room_type}</p>
                    <p><strong>💰 Цена за ночь:</strong> ${room.price_per_night} руб.</p>
                    <p><strong>👥 Вместимость:</strong> ${room.capacity} гостей</p>
                    <p><strong>📊 Статус:</strong> <span class="${statusClass}">${statusText}</span></p>
                    ${room.description ? `<p><strong>📝 Описание:</strong> ${room.description}</p>` : ''}
                    ${room.amenities ? `<p><strong>🎯 Удобства:</strong> ${room.amenities}</p>` : ''}
                    
                    <div class="card-actions">
                        <button class="btn btn-warning" onclick="app.editRoom(${room.id})">✏️ Редактировать</button>
                        <button class="btn btn-danger" onclick="app.deleteRoom(${room.id})">🗑️ Удалить</button>
                        <button class="btn" onclick="app.updateRoomStatus(${room.id})">🔄 Статус</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderBookings() {
        const container = document.getElementById('bookings-list');
        if (!container) return;
        
        if (!this.bookings.length) {
            container.innerHTML = '<p>📅 Бронирования не найдены. Создайте первое бронирование!</p>';
            return;
        }

        container.innerHTML = this.bookings.map(booking => {
            const user = this.users.find(u => u.id === booking.user_id);
            const hotel = this.hotels.find(h => h.id === booking.hotel_id);
            const room = this.rooms.find(r => r.id === booking.room_id);
            const statusText = this.getBookingStatusText(booking.status);
            
            return `
                <div class="card">
                    <h3>📋 Бронирование #${booking.booking_reference}</h3>
                    <p><strong>👤 Гость:</strong> ${user?.first_name || 'Неизвестно'} ${user?.last_name || ''}</p>
                    <p><strong>🏨 Отель:</strong> ${hotel?.name || 'Неизвестно'}</p>
                    <p><strong>🛏️ Комната:</strong> ${room?.room_number || 'Неизвестно'}</p>
                    <p><strong>📅 Заезд:</strong> ${UIUtils.formatDateTime(booking.check_in_date)}</p>
                    <p><strong>📅 Выезд:</strong> ${UIUtils.formatDateTime(booking.check_out_date)}</p>
                    <p><strong>👥 Гостей:</strong> ${booking.number_of_guests}</p>
                    <p><strong>💰 Общая цена:</strong> ${booking.total_price} руб.</p>
                    <p><strong>📊 Статус:</strong> ${statusText}</p>
                    ${booking.special_requests ? `<p><strong>💬 Пожелания:</strong> ${booking.special_requests}</p>` : ''}
                    
                    <div class="card-actions">
                        <button class="btn btn-success" onclick="app.checkInBooking(${booking.id})" 
                                ${booking.status !== 'confirmed' ? 'disabled' : ''}>
                            ✅ Заезд
                        </button>
                        <button class="btn btn-warning" onclick="app.checkOutBooking(${booking.id})" 
                                ${booking.status !== 'checked_in' ? 'disabled' : ''}>
                            🏁 Выезд
                        </button>
                        <button class="btn btn-danger" onclick="app.cancelBooking(${booking.id})" 
                                ${!['confirmed', 'checked_in'].includes(booking.status) ? 'disabled' : ''}>
                            ❌ Отменить
                        </button>
                        <button class="btn" onclick="app.deleteBooking(${booking.id})" 
                            style="background-color: #6c757d; color: white;">
                            🗑️ Удалить
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderGuests() {
        const container = document.getElementById('guests-list');
        if (!container) return;
        
        if (!this.users.length) {
            container.innerHTML = '<p>👥 Гости не найдены. Добавьте первого гостя!</p>';
            return;
        }

        container.innerHTML = this.users.map(user => {
            const activeBookings = this.bookings.filter(booking => 
                booking.user_id === user.id && 
                ['confirmed', 'checked_in'].includes(booking.status)
            ).length;

            return `
                <div class="card">
                    <h3>👤 ${user.first_name} ${user.last_name}</h3>
                    <p><strong>📧 Email:</strong> ${user.email}</p>
                    <p><strong>📞 Телефон:</strong> ${user.phone || 'Не указан'}</p>
                    <p><strong>📅 Зарегистрирован:</strong> ${UIUtils.formatDate(user.created_at)}</p>
                    
                    <div class="guest-stats">
                        <div class="stat-item">
                            <div class="stat-number">${activeBookings}</div>
                            <div class="stat-label">Активных</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">${this.bookings.filter(b => b.user_id === user.id).length}</div>
                            <div class="stat-label">Всего</div>
                        </div>
                    </div>
                    
                    <div class="card-actions">
                        <button class="btn btn-warning" onclick="app.editGuest(${user.id})">✏️ Редактировать</button>
                        <button class="btn btn-danger" onclick="app.deleteGuest(${user.id})">🗑️ Удалить</button>
                        <button class="btn" onclick="app.showGuestBookings(${user.id})">📋 Бронирования</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    getRoomStatusText(status) {
        const statusMap = {
            'available': '✅ Доступна',
            'occupied': '🔴 Занята',
            'maintenance': '🔧 На обслуживании',
            'cleaning': '🧹 Уборка'
        };
        return statusMap[status] || status;
    }

    getBookingStatusText(status) {
        const statusMap = {
            'confirmed': '✅ Подтверждено',
            'cancelled': '❌ Отменено',
            'completed': '🏁 Завершено',
            'checked_in': '🏠 Заселен',
            'checked_out': '🚪 Выселен'
        };
        return statusMap[status] || status;
    }

    // Методы для работы с отелями
    showHotelForm(hotel = null) {
        const isEdit = !!hotel;
        const title = isEdit ? '✏️ Редактировать отель' : '🏨 Добавить отель';
        
        const content = `
            <form id="hotel-form">
                <div class="form-group">
                    <label>Название отеля:</label>
                    <input type="text" name="name" value="${hotel?.name || ''}" required>
                </div>
                <div class="form-group">
                    <label>Описание:</label>
                    <textarea name="description" placeholder="Описание отеля...">${hotel?.description || ''}</textarea>
                </div>
                <div class="form-group">
                    <label>Адрес:</label>
                    <input type="text" name="address" value="${hotel?.address || ''}" required>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Город:</label>
                        <input type="text" name="city" value="${hotel?.city || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>Страна:</label>
                        <input type="text" name="country" value="${hotel?.country || ''}" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Рейтинг:</label>
                    <input type="number" name="rating" step="0.1" min="0" max="5" 
                           value="${hotel?.rating || 0}" placeholder="0.0">
                </div>
                <div class="card-actions">
                    <button type="button" class="btn btn-primary" onclick="app.saveHotel(${hotel?.id || null})">
                        ${isEdit ? '💾 Обновить' : '➕ Создать'}
                    </button>
                    <button type="button" class="btn" onclick="closeModal()">❌ Отмена</button>
                </div>
            </form>
        `;
        
        showModal(title, content);
    }

    async saveHotel(hotelId = null) {
        try {
            const formData = FormUtils.getFormData('hotel-form');
            
            if (hotelId) {
                await ApiClient.put(`/hotels/${hotelId}`, formData);
                UIUtils.showMessage('✅ Отель успешно обновлен');
            } else {
                await ApiClient.post('/hotels/', formData);
                UIUtils.showMessage('✅ Отель успешно создан');
            }
            
            closeModal();
            await this.loadHotels();
        } catch (error) {
            UIUtils.showMessage(`❌ Ошибка при сохранении отеля: ${error.message}`, 'error');
        }
    }

    async editHotel(hotelId) {
        const hotel = this.hotels.find(h => h.id === hotelId);
        if (hotel) {
            this.showHotelForm(hotel);
        }
    }

    async deleteHotel(hotelId) {
        if (confirm('❌ Вы уверены, что хотите удалить этот отель?')) {
            try {
                await ApiClient.delete(`/hotels/${hotelId}`);
                UIUtils.showMessage('✅ Отель успешно удален');
                await this.loadHotels();
            } catch (error) {
                UIUtils.showMessage(`❌ Ошибка при удалении отеля: ${error.message}`, 'error');
            }
        }
    }

    // Методы для работы с гостями
    showGuestForm(user = null) {
        const isEdit = !!user;
        const title = isEdit ? '✏️ Редактировать гостя' : '👥 Добавить гостя';
        
        const content = `
            <form id="guest-form">
                <div class="form-row">
                    <div class="form-group">
                        <label>Имя:</label>
                        <input type="text" name="first_name" value="${user?.first_name || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>Фамилия:</label>
                        <input type="text" name="last_name" value="${user?.last_name || ''}" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" name="email" value="${user?.email || ''}" required>
                </div>
                <div class="form-group">
                    <label>Телефон:</label>
                    <input type="tel" name="phone" value="${user?.phone || ''}" placeholder="+7 (XXX) XXX-XX-XX">
                </div>
                <div class="card-actions">
                    <button type="button" class="btn btn-primary" onclick="app.saveGuest(${user?.id || null})">
                        ${isEdit ? '💾 Обновить' : '➕ Создать'}
                    </button>
                    <button type="button" class="btn" onclick="closeModal()">❌ Отмена</button>
                </div>
            </form>
        `;
        
        showModal(title, content);
    }

    async saveGuest(userId = null) {
        try {
            const formData = FormUtils.getFormData('guest-form');
            
            if (userId) {
                await ApiClient.put(`/users/${userId}`, formData);
                UIUtils.showMessage('✅ Гость успешно обновлен');
            } else {
                await ApiClient.post('/users/', formData);
                UIUtils.showMessage('✅ Гость успешно создан');
            }
            
            closeModal();
            await this.loadUsers();
        } catch (error) {
            UIUtils.showMessage(`❌ Ошибка при сохранении гостя: ${error.message}`, 'error');
        }
    }

    async editGuest(userId) {
        const user = this.users.find(u => u.id === userId);
        if (user) {
            this.showGuestForm(user);
        }
    }

    async deleteGuest(userId) {
        if (confirm('❌ Вы уверены, что хотите удалить этого гостя?')) {
            try {
                await ApiClient.delete(`/users/${userId}`);
                UIUtils.showMessage('✅ Гость успешно удален');
                await this.loadUsers();
            } catch (error) {
                UIUtils.showMessage(`❌ Ошибка при удалении гостя: ${error.message}`, 'error');
            }
        }
    }

    showGuestBookings(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        const userBookings = this.bookings.filter(booking => booking.user_id === userId);
        
        let content;
        if (!userBookings.length) {
            content = `<p>📭 У гостя нет бронирований</p>`;
        } else {
            content = `
                <div class="bookings-list">
                    <h4>📋 Бронирования гостя ${user.first_name} ${user.last_name}</h4>
                    ${userBookings.map(booking => {
                        const hotel = this.hotels.find(h => h.id === booking.hotel_id);
                        const room = this.rooms.find(r => r.id === booking.room_id);
                        
                        return `
                            <div class="booking-item">
                                <p><strong>🏨 Отель:</strong> ${hotel?.name || 'Неизвестно'}</p>
                                <p><strong>🛏️ Комната:</strong> ${room?.room_number || 'Неизвестно'}</p>
                                <p><strong>📅 Даты:</strong> ${UIUtils.formatDate(booking.check_in_date)} - ${UIUtils.formatDate(booking.check_out_date)}</p>
                                <p><strong>📊 Статус:</strong> ${this.getBookingStatusText(booking.status)}</p>
                                <p><strong>💰 Стоимость:</strong> ${booking.total_price} руб.</p>
                                <p><strong>🔢 Номер бронирования:</strong> ${booking.booking_reference}</p>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }
        
        showModal(`📋 Бронирования гостя ${user.first_name} ${user.last_name}`, content);
    }

    // Методы для работы с комнатами (будут в rooms.js)
    async editRoom(roomId) {
        const room = this.rooms.find(r => r.id === roomId);
        if (room) {
            showRoomForm(room);
        }
    }

    async deleteRoom(roomId) {
        if (confirm('❌ Вы уверены, что хотите удалить эту комнату?')) {
            try {
                await ApiClient.delete(`/rooms/${roomId}`);
                UIUtils.showMessage('✅ Комната успешно удалена');
                await this.loadRooms();
            } catch (error) {
                UIUtils.showMessage(`❌ Ошибка при удалении комнаты: ${error.message}`, 'error');
            }
        }
    }

    async updateRoomStatus(roomId) {
        const room = this.rooms.find(r => r.id === roomId);
        if (!room) return;
        
        const content = `
            <form id="status-form">
                <div class="form-group">
                    <label>Новый статус:</label>
                    <select name="status">
                        <option value="available" ${room.status === 'available' ? 'selected' : ''}>✅ Доступна</option>
                        <option value="occupied" ${room.status === 'occupied' ? 'selected' : ''}>🔴 Занята</option>
                        <option value="maintenance" ${room.status === 'maintenance' ? 'selected' : ''}>🔧 На обслуживании</option>
                        <option value="cleaning" ${room.status === 'cleaning' ? 'selected' : ''}>🧹 Уборка</option>
                    </select>
                </div>
                <div class="card-actions">
                    <button type="button" class="btn btn-primary" onclick="saveRoomStatus(${roomId})">💾 Обновить статус</button>
                    <button type="button" class="btn" onclick="closeModal()">❌ Отмена</button>
                </div>
            </form>
        `;
        
        showModal('🔄 Изменить статус комнаты', content);
    }

    // Методы для работы с бронированиями (будут в bookings.js)
    async checkInBooking(bookingId) {
        try {
            await ApiClient.put(`/bookings/${bookingId}/check-in`);
            UIUtils.showMessage('✅ Заезд успешно зарегистрирован');
            await this.loadBookings();
        } catch (error) {
            UIUtils.showMessage(`❌ Ошибка при регистрации заезда: ${error.message}`, 'error');
        }
    }

    async checkOutBooking(bookingId) {
        try {
            await ApiClient.put(`/bookings/${bookingId}/check-out`);
            UIUtils.showMessage('✅ Выезд успешно зарегистрирован');
            await this.loadBookings();
        } catch (error) {
            UIUtils.showMessage(`❌ Ошибка при регистрации выезда: ${error.message}`, 'error');
        }
    }

    async cancelBooking(bookingId) {
        if (confirm('❌ Вы уверены, что хотите отменить это бронирование?')) {
            try {
                await ApiClient.put(`/bookings/${bookingId}/cancel`);
                UIUtils.showMessage('✅ Бронирование успешно отменено');
                await this.loadBookings();
            } catch (error) {
                UIUtils.showMessage(`❌ Ошибка при отмене бронирования: ${error.message}`, 'error');
            }
        }
    }
    async deleteBooking(booking_id) {
        if (confirm('❌ Вы уверены, что хотите удалить это бронирование?')) {
            try {
                await ApiClient.delete(`/bookings/${booking_id}`);
                UIUtils.showMessage('✅ Бронирование успешно удалено');
                await app.loadBookings();
            } catch (error) {
                UIUtils.showMessage('❌ Ошибка при удалении бронирования', 'error');
            }
        }
    }
}



// Глобальные функции
function showModal(title, content) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-content').innerHTML = content;
    document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

let app;

document.addEventListener('DOMContentLoaded', () => {
    app = new HotelBookingApp();
    window.app = app;
});

// Глобальные функции для кнопок
window.showHotelForm = () => app?.showHotelForm();
window.showGuestForm = () => app?.showGuestForm();
window.showRoomForm = () => showRoomForm();
window.showBookingForm = () => showBookingForm();