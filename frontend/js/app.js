class HotelBookingApp {
    constructor() {
        this.currentTab = 'auth';
        this.hotels = [];
        this.rooms = [];
        this.bookings = [];
        this.users = [];
        this.currentUser = null;
        this.currentUser = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
    }

    checkAuthStatus() {
        this.currentUser = AuthManager.getCurrentUser();
        if (this.currentUser) {
            this.showApp();
        } else {
            this.showAuth();
        }
    }

    showApp() {
        this.currentTab = 'hotels';
        this.updateUIForUserRole();
        //this.loadInitialData();
        //this.showTab('hotels');
        document.getElementById('auth-tab').classList.remove('active');
        this.updateAuthUI();
    }

    showAuth() {
        this.currentTab = 'auth';
        document.getElementById('auth-tab').classList.add('active');
        // Скрываем все остальные табы
        document.querySelectorAll('.tab-content').forEach(tab => {
            if (tab.id !== 'auth-tab') {
                tab.classList.remove('active');
            }
        });
        this.updateAuthUI();
        this.checkAuthStatus();
    }

    checkAuthStatus() {
        this.currentUser = AuthManager.getCurrentUser();
        if (this.currentUser) {
            this.showApp();
        } else {
            this.showAuth();
        }
    }

    setupEventListeners() {
        // Навигация
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                if (!AuthManager.isAuthenticated()) {
                    this.showAuth();
                    return;
                }
                const tab = e.target.getAttribute('data-tab');
                this.showTab(tab);
            });
        });

        // Форма входа
        document.getElementById('login-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Обновляем панель авторизации
        this.updateAuthUI();
    }

    async handleLogin() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        if (!email || !password) {
            UIUtils.showMessage('Заполните все поля', 'error');
            return;
        }

        try {
            UIUtils.showMessage('Выполняется вход...', 'success');
            
            // Используем диагностическую версию логина
            const user = await AuthManager.loginWithDiagnosis(email, password);
            this.currentUser = user;
            
            UIUtils.showMessage(`Добро пожаловать, ${user.first_name}!`);
            this.showApp();
        } catch (error) {
            console.error('💥 Final login error:', error);
            
            let errorMessage = 'Ошибка входа';
            if (error.message.includes('422')) {
                errorMessage = 'Ошибка валидации на сервере. Сервер ожидает другие данные.';
            } else if (error.message.includes('404')) {
                errorMessage = 'Сервер не найден или endpoint недоступен.';
            } else if (error.message.includes('Network Error')) {
                errorMessage = 'Проблемы с сетью. Проверьте подключение к интернету.';
            } else {
                errorMessage = error.message;
            }
            
            UIUtils.showMessage(errorMessage, 'error');
        }
    }

    updateAuthUI() {
        const authContainer = document.getElementById('nav-auth');
        if (!authContainer) return;

        if (this.currentUser) {
            authContainer.innerHTML = `
                <div class="user-info">
                    <span>👤 ${this.currentUser.first_name} ${this.currentUser.last_name}</span>
                    <span class="user-role">(${this.currentUser.role === 'admin' ? 'Администратор' : 'Пользователь'})</span>
                    <button class="btn btn-outline" onclick="app.logout()">Выйти</button>
                </div>
            `;
        } else {
            authContainer.innerHTML = `
                <button class="btn btn-outline" onclick="app.showAuth()">Войти</button>
            `;
        }
    }

    updateUIForUserRole() {
        const isAdmin = AuthManager.isAdmin();
        
        // Показываем/скрываем кнопки в зависимости от роли
        const addHotelBtn = document.getElementById('add-hotel-btn');
        const addRoomBtn = document.getElementById('add-room-btn');
        const addGuestBtn = document.getElementById('add-guest-btn');
        const addBookingBtn = document.getElementById('add-booking-btn');
        
        if (addHotelBtn) addHotelBtn.style.display = isAdmin ? 'block' : 'none';
        if (addRoomBtn) addRoomBtn.style.display = isAdmin ? 'block' : 'none';
        if (addGuestBtn) addGuestBtn.style.display = isAdmin ? 'block' : 'none';
        if (addBookingBtn) addBookingBtn.style.display = AuthManager.isAuthenticated() ? 'block' : 'none';
        
        // Обновляем навигацию
        const guestsTab = document.querySelector('[data-tab="guests"]');
        const hotelsTab = document.querySelector('[data-tab="hotels"]');
        const roomsTab = document.querySelector('[data-tab="rooms"]');
        
        if (guestsTab) guestsTab.style.display = isAdmin ? 'block' : 'none';
        if (hotelsTab) hotelsTab.style.display = isAdmin ? 'block' : 'flex';
        if (roomsTab) roomsTab.style.display = isAdmin ? 'block' : 'flex';
    }

    logout() {
        AuthManager.logout();
        this.currentUser = null;
        this.showAuth();
        UIUtils.showMessage('Вы вышли из системы');
    }

    async loadInitialData() {
        if (!AuthManager.isAuthenticated()) return;
        
        console.log('🚀 Starting initial data load...');
        
        try {
            // Загружаем пользователей с обработкой ошибок
            await this.loadUsersWithRetry();
            
            // Загружаем остальные данные
            await Promise.all([
                this.loadHotels(),
                this.loadRooms(),
                this.loadBookings()
            ]);
            
            console.log('✅ All data loaded successfully');
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
            UIUtils.showMessage('Ошибка загрузки данных: ' + error.message, 'error');
        }
    }

    async loadUsersWithRetry() {
        try {
            console.log('👥 Loading users from API...');
            this.users = await ApiClient.get('/users/');
            this.usersLoadAttempted = true;
            console.log(`✅ Loaded ${this.users.length} users from API`);
            this.renderGuests();
        } catch (error) {
            console.error('❌ Failed to load users from API:', error);
            this.usersLoadAttempted = true;
            
            // Пробуем альтернативный эндпоинт
            try {
                console.log('🔄 Retrying with alternative endpoint /users...');
                this.users = await ApiClient.get('/users');
                console.log(`✅ Loaded ${this.users.length} users from alternative endpoint`);
                this.renderGuests();
            } catch (retryError) {
                console.error('❌ Alternative endpoint also failed:', retryError);
                
                // Создаем fallback список пользователей
                this.createFallbackUsers();
                this.renderGuests();
                
                throw new Error('Не удалось загрузить пользователей с сервера');
            }
        }
    }

    createFallbackUsers() {
        console.log('🔄 Creating fallback users list...');
        
        // Fallback пользователи на основе текущего пользователя
        const currentUser = this.currentUser;
        if (currentUser) {
            this.users = [currentUser];
            console.log(`✅ Created fallback with current user: ${currentUser.email}`);
        } else {
            // Если нет текущего пользователя, создаем базовый список
            this.users = [
                {
                    id: 1,
                    email: 'admin@hotels.com',
                    first_name: 'Администратор',
                    last_name: 'Системы',
                    phone: '+79990000000',
                    role: 'admin',
                    created_at: new Date().toISOString()
                }
            ];
            console.log(`✅ Created basic fallback users list`);
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
            // throw error;
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
            // throw error;
        }
    }

    async loadBookings() {
        try {
            console.log('📅 Loading bookings...');
            const isAdmin = AuthManager.isAdmin();
            const currentUserId = this.currentUser?.id;
            
            if (isAdmin) {
                // Администраторы видят все бронирования
                this.bookings = await ApiClient.get('/bookings/');
            } else {
                // Пользователи видят только свои бронирования
                this.bookings = await ApiClient.get(`/bookings/user/${currentUserId}/bookings`);
            }
            console.log(`✅ Loaded ${this.bookings.length} bookings`);
            this.renderBookings();
        } catch (error) {
            console.error('❌ Error loading bookings:', error);
            // throw error;
        }
    }

    async loadUsers() {
        try {
            console.log('👥 Loading users (direct call)...');
            this.users = await ApiClient.get('/users/');
            console.log(`✅ Loaded ${this.users.length} users`);
            this.renderGuests();
        } catch (error) {
            console.error('❌ Error loading users:', error);
            this.renderGuestsError(error);
        }
    }

    renderGuestsError(error) {
        const container = document.getElementById('guests-list');
        if (!container) return;

        const isAdmin = AuthManager.isAdmin();
        
        if (!isAdmin) {
            // Для обычных пользователей показываем только их профиль
            const currentUser = this.currentUser;
            if (currentUser) {
                container.innerHTML = `
                    <div class="card">
                        <h3>👤 ${currentUser.first_name} ${currentUser.last_name}</h3>
                        <p><strong>📧 Email:</strong> ${currentUser.email}</p>
                        <p><strong>📞 Телефон:</strong> ${currentUser.phone || 'Не указан'}</p>
                        <p><strong>🎯 Роль:</strong> ${currentUser.role === 'admin' ? 'Администратор' : 'Пользователь'}</p>
                        <p class="error-message">⚠️ Не удалось загрузить полный список пользователей: ${error.message}</p>
                        <div class="card-actions">
                            <button class="btn btn-warning" onclick="app.editGuest(${currentUser.id})">✏️ Редактировать профиль</button>
                            <button class="btn" onclick="app.showGuestBookings(${currentUser.id})">📋 Мои бронирования</button>
                        </div>
                    </div>
                `;
            }
        } else {
            // Для администраторов показываем ошибку
            container.innerHTML = `
                <div class="card error-card">
                    <h3>⚠️ Ошибка загрузки пользователей</h3>
                    <p>Не удалось загрузить список пользователей.</p>
                    <p><strong>Ошибка:</strong> ${error.message}</p>
                    <p>Возможные причины:</p>
                    <ul>
                        <li>Проблемы с подключением к серверу</li>
                        <li>Недостаточно прав для просмотра пользователей</li>
                        <li>Ошибка валидации на сервере</li>
                    </ul>
                    <div class="card-actions">
                        <button class="btn btn-primary" onclick="app.loadUsers()">🔄 Повторить попытку</button>
                        <button class="btn" onclick="app.createFallbackUsers()">🛠️ Использовать резервный список</button>
                    </div>
                </div>
            `;
        }
    }

    showTab(tabName) {
        if (!AuthManager.isAuthenticated()) {
            this.showAuth();
            return;
        }

        // Скрыть все табы
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Убрать активный класс со всех кнопок
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Показать выбранный таб
        const tabElement = document.getElementById(`${tabName}-tab`);
        if (tabElement) {
            tabElement.classList.add('active');
        }
        
        const linkElement = document.querySelector(`[data-tab="${tabName}"]`);
        if (linkElement) {
            linkElement.classList.add('active');
        }
        
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
            container.innerHTML = '<p>🏨 Отели не найдены</p>';
            return;
        }

        const isAdmin = AuthManager.isAdmin();

        container.innerHTML = this.hotels.map(hotel => `
            <div class="card">
                <h3>${hotel.name}</h3>
                <p><strong>📍 Адрес:</strong> ${hotel.address}</p>
                <p><strong>🏙️ Город:</strong> ${hotel.city}, ${hotel.country}</p>
                <p><strong>⭐ Рейтинг:</strong> ${hotel.rating || 'Нет оценки'}</p>
                ${hotel.description ? `<p><strong>📝 Описание:</strong> ${hotel.description}</p>` : ''}
                <p><strong>📅 Создан:</strong> ${UIUtils.formatDate(hotel.created_at)}</p>
                
                ${isAdmin ? `
                    <div class="card-actions">
                        <button class="btn btn-warning" onclick="app.editHotel(${hotel.id})">✏️ Редактировать</button>
                        <button class="btn btn-danger" onclick="app.deleteHotel(${hotel.id})">🗑️ Удалить</button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    renderRooms() {
        const container = document.getElementById('rooms-list');
        if (!container) return;
        
        if (!this.rooms.length) {
            container.innerHTML = '<p>🛏️ Комнаты не найдены</p>';
            return;
        }

        const isAdmin = AuthManager.isAdmin();

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
                    
                    ${isAdmin ? `
                        <div class="card-actions">
                            <button class="btn btn-warning" onclick="app.editRoom(${room.id})">✏️ Редактировать</button>
                            <button class="btn btn-danger" onclick="app.deleteRoom(${room.id})">🗑️ Удалить</button>
                            <button class="btn" onclick="app.updateRoomStatus(${room.id})">🔄 Статус</button>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    renderBookings() {
        const container = document.getElementById('bookings-list');
        if (!container) return;
        
        if (!this.bookings.length) {
            container.innerHTML = '<p>📅 Бронирования не найдены</p>';
            return;
        }

        const isAdmin = AuthManager.isAdmin();

        container.innerHTML = this.bookings.map(booking => {
            const user = this.users.find(u => u.id === booking.user_id);
            const hotel = this.hotels.find(h => h.id === booking.hotel_id);
            const room = this.rooms.find(r => r.id === booking.room_id);
            const statusText = this.getBookingStatusText(booking.status);
            
            return `
                <div class="card">
                    <h3>📋 Бронирование #${booking.booking_reference}</h3>
                    ${isAdmin ? `<p><strong>👤 Гость:</strong> ${user?.first_name || 'Неизвестно'} ${user?.last_name || ''}</p>` : ''}
                    <p><strong>🏨 Отель:</strong> ${hotel?.name || 'Неизвестно'}</p>
                    <p><strong>🛏️ Комната:</strong> ${room?.room_number || 'Неизвестно'}</p>
                    <p><strong>📅 Заезд:</strong> ${UIUtils.formatDateTime(booking.check_in_date)}</p>
                    <p><strong>📅 Выезд:</strong> ${UIUtils.formatDateTime(booking.check_out_date)}</p>
                    <p><strong>👥 Гостей:</strong> ${booking.number_of_guests}</p>
                    <p><strong>💰 Общая цена:</strong> ${booking.total_price} руб.</p>
                    <p><strong>📊 Статус:</strong> ${statusText}</p>
                    ${booking.special_requests ? `<p><strong>💬 Пожелания:</strong> ${booking.special_requests}</p>` : ''}
                    
                    <div class="card-actions">
                        ${isAdmin ? `
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
                        ` : `
                            <button class="btn btn-danger" onclick="app.cancelBooking(${booking.id})" 
                                    ${!['confirmed', 'checked_in'].includes(booking.status) ? 'disabled' : ''}>
                                ❌ Отменить бронирование
                            </button>
                        `}
                    </div>
                </div>
            `;
        }).join('');
    }

    renderGuests() {
        const container = document.getElementById('guests-list');
        if (!container) return;
        
        if (!this.users.length) {
            container.innerHTML = '<p>👥 Гости не найдены</p>';
            return;
        }

        const isAdmin = AuthManager.isAdmin();
        const currentUserId = this.currentUser?.id;

        container.innerHTML = this.users.map(user => {
            // Пользователи видят только себя, админы видят всех
            if (!isAdmin && user.id !== currentUserId) {
                return '';
            }

            const activeBookings = this.bookings.filter(booking => 
                booking.user_id === user.id && 
                ['confirmed', 'checked_in'].includes(booking.status)
            ).length;

            return `
                <div class="card">
                    <h3>👤 ${user.first_name} ${user.last_name}</h3>
                    <p><strong>📧 Email:</strong> ${user.email}</p>
                    <p><strong>📞 Телефон:</strong> ${user.phone || 'Не указан'}</p>
                    <p><strong>🎯 Роль:</strong> ${user.role === 'admin' ? 'Администратор' : 'Пользователь'}</p>
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
                    
                    ${isAdmin ? `
                        <div class="card-actions">
                            <button class="btn btn-warning" onclick="app.editGuest(${user.id})">✏️ Редактировать</button>
                            <button class="btn btn-danger" onclick="app.deleteGuest(${user.id})">🗑️ Удалить</button>
                            <button class="btn" onclick="app.showGuestBookings(${user.id})">📋 Бронирования</button>
                        </div>
                    ` : `
                        <div class="card-actions">
                            <button class="btn btn-warning" onclick="app.editGuest(${user.id})">✏️ Редактировать профиль</button>
                            <button class="btn" onclick="app.showGuestBookings(${user.id})">📋 Мои бронирования</button>
                        </div>
                    `}
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
        if (!AuthManager.isAdmin()) {
            UIUtils.showMessage('Недостаточно прав для управления отелями', 'error');
            return;
        }

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
        const isAdmin = AuthManager.isAdmin();
        const currentUserId = this.currentUser?.id;

        // Проверяем права: пользователи могут редактировать только свой профиль
        if (!isAdmin && user && user.id !== currentUserId) {
            UIUtils.showMessage('Недостаточно прав для редактирования этого профиля', 'error');
            return;
        }

        const title = isEdit ? '✏️ Редактировать профиль' : '👥 Добавить гостя';
        
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
                ${isAdmin && !isEdit ? `
                    <div class="form-group">
                        <label>Роль:</label>
                        <select name="role">
                            <option value="user">Пользователь</option>
                            <option value="admin">Администратор</option>
                        </select>
                    </div>
                ` : ''}
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
            const isAdmin = AuthManager.isAdmin();
            
            // Пользователи не могут менять свою роль
            if (!isAdmin && formData.role) {
                delete formData.role;
            }
            
            if (userId) {
                await ApiClient.put(`/users/${userId}`, formData);
                UIUtils.showMessage('✅ Профиль успешно обновлен');
                
                // Если пользователь обновил свой профиль, обновляем данные
                if (userId === this.currentUser?.id) {
                    const updatedUser = await ApiClient.get(`/users/${userId}`);
                    AuthManager.setCurrentUser(updatedUser);
                    this.currentUser = updatedUser;
                    this.updateAuthUI();
                }
            } else {
                await ApiClient.post('/users/', formData);
                UIUtils.showMessage('✅ Гость успешно создан');
            }
            
            closeModal();
            await this.loadUsers();
        } catch (error) {
            UIUtils.showMessage(`❌ Ошибка при сохранении: ${error.message}`, 'error');
        }
    }

    async editGuest(userId) {
        const user = this.users.find(u => u.id === userId);
        if (user) {
            this.showGuestForm(user);
        }
    }

    async deleteGuest(userId) {
        if (confirm('❌ Вы уверены, что хотите удалить этого пользователя?')) {
            try {
                await ApiClient.delete(`/users/${userId}`);
                UIUtils.showMessage('✅ Пользователь успешно удален');
                
                // Если пользователь удалил свой аккаунт, выходим
                if (userId === this.currentUser?.id) {
                    this.logout();
                } else {
                    await this.loadUsers();
                }
            } catch (error) {
                UIUtils.showMessage(`❌ Ошибка при удалении: ${error.message}`, 'error');
            }
        }
    }

    showGuestBookings(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        const userBookings = this.bookings.filter(booking => booking.user_id === userId);
        const isAdmin = AuthManager.isAdmin();
        const isOwnProfile = userId === this.currentUser?.id;
        
        let content;
        if (!userBookings.length) {
            content = `<p>📭 ${isOwnProfile ? 'У вас нет бронирований' : 'У гостя нет бронирований'}</p>`;
        } else {
            content = `
                <div class="bookings-list">
                    <h4>📋 ${isOwnProfile ? 'Мои бронирования' : `Бронирования гостя ${user.first_name} ${user.last_name}`}</h4>
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
        
        showModal(`📋 ${isOwnProfile ? 'Мои бронирования' : `Бронирования гостя ${user.first_name} ${user.last_name}`}`, content);
    }

    // Методы для работы с комнатами
    async editRoom(roomId) {
        if (!AuthManager.isAdmin()) {
            UIUtils.showMessage('Недостаточно прав для редактирования комнат', 'error');
            return;
        }
        const room = this.rooms.find(r => r.id === roomId);
        if (room) {
            showRoomForm(room);
        }
    }

    async deleteRoom(roomId) {
        if (!AuthManager.isAdmin()) {
            UIUtils.showMessage('Недостаточно прав для удаления комнат', 'error');
            return;
        }
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
        if (!AuthManager.isAdmin()) {
            UIUtils.showMessage('Недостаточно прав для изменения статуса комнат', 'error');
            return;
        }
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

    // Методы для работы с бронированиями
    async checkInBooking(bookingId) {
        if (!AuthManager.isAdmin()) {
            UIUtils.showMessage('Недостаточно прав для регистрации заезда', 'error');
            return;
        }
        try {
            await ApiClient.put(`/bookings/${bookingId}/check-in`);
            UIUtils.showMessage('✅ Заезд успешно зарегистрирован');
            await this.loadBookings();
        } catch (error) {
            UIUtils.showMessage(`❌ Ошибка при регистрации заезда: ${error.message}`, 'error');
        }
    }

    async checkOutBooking(bookingId) {
        if (!AuthManager.isAdmin()) {
            UIUtils.showMessage('Недостаточно прав для регистрации выезда', 'error');
            return;
        }
        try {
            await ApiClient.put(`/bookings/${bookingId}/check-out`);
            UIUtils.showMessage('✅ Выезд успешно зарегистрирован');
            await this.loadBookings();
        } catch (error) {
            UIUtils.showMessage(`❌ Ошибка при регистрации выезда: ${error.message}`, 'error');
        }
    }

    async cancelBooking(bookingId) {
        const booking = this.bookings.find(b => b.id === bookingId);
        if (!booking) return;

        const isAdmin = AuthManager.isAdmin();
        const isOwnBooking = booking.user_id === this.currentUser?.id;

        if (!isAdmin && !isOwnBooking) {
            UIUtils.showMessage('Недостаточно прав для отмены этого бронирования', 'error');
            return;
        }

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

    async deleteBooking(bookingId) {
        if (!AuthManager.isAdmin()) {
            UIUtils.showMessage('Недостаточно прав для удаления бронирований', 'error');
            return;
        }
        if (confirm('❌ Вы уверены, что хотите удалить это бронирование?')) {
            try {
                await ApiClient.delete(`/bookings/${bookingId}`);
                UIUtils.showMessage('✅ Бронирование успешно удалено');
                await this.loadBookings();
            } catch (error) {
                UIUtils.showMessage(`❌ Ошибка при удалении бронирования: ${error.message}`, 'error');
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

function showRegisterForm() {
    const content = `
        <form id="register-form">
            <div class="form-row">
                <div class="form-group">
                    <label>Имя:</label>
                    <input type="text" name="first_name" required>
                </div>
                <div class="form-group">
                    <label>Фамилия:</label>
                    <input type="text" name="last_name" required>
                </div>
            </div>
            <div class="form-group">
                <label>Email:</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>Телефон:</label>
                <input type="tel" name="phone" placeholder="+7 (XXX) XXX-XX-XX">
            </div>
            <div class="card-actions">
                <button type="button" class="btn btn-primary" onclick="registerUser()">Зарегистрироваться</button>
                <button type="button" class="btn" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    `;
    
    showModal('Регистрация', content);
}

async function registerUser() {
    try {
        const formData = FormUtils.getFormData('register-form');
        const user = await AuthManager.register(formData);
        UIUtils.showMessage(`Регистрация успешна! Добро пожаловать, ${user.first_name}!`);
        closeModal();
        window.app.currentUser = user;
        window.app.showApp();
    } catch (error) {
        UIUtils.showMessage('Ошибка регистрации: ' + error.message, 'error');
    }
}

let app;

document.addEventListener('DOMContentLoaded', () => {
    app = new HotelBookingApp();
    window.app = app;
});

// Глобальные функции для кнопок
window.showHotelForm = () => app?.showHotelForm();
window.showGuestForm = () => app?.showGuestForm();
window.showRoomForm = () => {
    if (!AuthManager.isAdmin()) {
        UIUtils.showMessage('Недостаточно прав для создания комнат', 'error');
        return;
    }
    showRoomForm();
};
window.showBookingForm = () => {
    if (!AuthManager.isAuthenticated()) {
        UIUtils.showMessage('Для создания бронирования необходимо войти в систему', 'error');
        return;
    }
    showBookingForm();
};