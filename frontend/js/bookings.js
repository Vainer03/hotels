function renderBookings() {
    const container = document.getElementById('bookings-list');
    
    if (!app.bookings.length) {
        container.innerHTML = '<p>Бронирования не найдены</p>';
        return;
    }

    container.innerHTML = app.bookings.map(booking => {
        const user = app.users.find(u => u.id === booking.user_id);
        const hotel = app.hotels.find(h => h.id === booking.hotel_id);
        const room = app.rooms.find(r => r.id === booking.room_id);
        
        return `
            <div class="card">
                <h3>Бронирование #${booking.booking_reference}</h3>
                <p><strong>Гость:</strong> ${user?.first_name || 'Неизвестно'} ${user?.last_name || ''}</p>
                <p><strong>Отель:</strong> ${hotel?.name || 'Неизвестно'}</p>
                <p><strong>Комната:</strong> ${room?.room_number || 'Неизвестно'}</p>
                <p><strong>Заезд:</strong> ${UIUtils.formatDateTime(booking.check_in_date)}</p>
                <p><strong>Выезд:</strong> ${UIUtils.formatDateTime(booking.check_out_date)}</p>
                <p><strong>Гостей:</strong> ${booking.number_of_guests}</p>
                <p><strong>Общая цена:</strong> ${booking.total_price} руб.</p>
                <p><strong>Статус:</strong> ${getBookingStatusText(booking.status)}</p>
                ${booking.special_requests ? `<p><strong>Особые пожелания:</strong> ${booking.special_requests}</p>` : ''}
                
                <div class="card-actions">
                    <button class="btn btn-success" onclick="checkInBooking(${booking.id})" ${booking.status !== 'confirmed' ? 'disabled' : ''}>✅ Заезд</button>
                    <button class="btn btn-warning" onclick="checkOutBooking(${booking.id})" ${booking.status !== 'checked_in' ? 'disabled' : ''}>🏁 Выезд</button>
                    <button class="btn btn-danger" onclick="cancelBooking(${booking.id})" ${!['confirmed', 'checked_in'].includes(booking.status) ? 'disabled' : ''}>❌ Отменить</button>
                    <button class="btn" onclick="deleteBooking(${booking.id})" style="background-color: #6c757d; color: white;">🗑️ Удалить</button>
                </div>
            </div>
        `;
    }).join('');
}

function getBookingStatusText(status) {
    const statusMap = {
        'confirmed': 'Подтверждено',
        'cancelled': 'Отменено',
        'completed': 'Завершено',
        'checked_in': 'Заселен',
        'checked_out': 'Выселен'
    };
    return statusMap[status] || status;
}

function showBookingForm() {
    const usersOptions = app.users.map(user => 
        `<option value="${user.id}">${user.first_name} ${user.last_name} (${user.email})</option>`
    ).join('');
    
    const hotelsOptions = app.hotels.map(hotel => 
        `<option value="${hotel.id}">${hotel.name} - ${hotel.city}</option>`
    ).join('');
    
    const availableRooms = app.rooms.filter(room => room.status === 'available');
    const roomsOptions = availableRooms.map(room => {
        const hotel = app.hotels.find(h => h.id === room.hotel_id);
        return `<option value="${room.id}">Комната ${room.room_number} (${hotel?.name}) - ${room.price_per_night} руб./ночь</option>`;
    }).join('');
    
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const checkinDefault = tomorrow.toISOString().slice(0, 16);
    
    const dayAfterTomorrow = new Date();
    dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 3);
    const checkoutDefault = dayAfterTomorrow.toISOString().slice(0, 16);
    
    const content = `
        <form id="booking-form">
            <div class="form-group">
                <label>Гость:</label>
                <select name="user_id" required>
                    <option value="">Выберите гостя</option>
                    ${usersOptions}
                </select>
            </div>
            <div class="form-group">
                <label>Отель:</label>
                <select name="hotel_id" required onchange="updateAvailableRooms(this.value)">
                    <option value="">Выберите отель</option>
                    ${hotelsOptions}
                </select>
            </div>
            <div class="form-group">
                <label>Комната:</label>
                <select name="room_id" required id="room-select">
                    <option value="">Сначала выберите отель</option>
                    ${roomsOptions}
                </select>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Дата заезда:</label>
                    <input type="datetime-local" name="check_in_date" value="${checkinDefault}" required>
                </div>
                <div class="form-group">
                    <label>Дата выезда:</label>
                    <input type="datetime-local" name="check_out_date" value="${checkoutDefault}" required>
                </div>
            </div>
            <div class="form-group">
                <label>Количество гостей:</label>
                <input type="number" name="number_of_guests" value="2" min="1" required>
            </div>
            <div class="form-group">
                <label>Особые пожелания:</label>
                <textarea name="special_requests" placeholder="Поздний заезд, дополнительные полотенца..."></textarea>
            </div>
            <div class="card-actions">
                <button type="button" class="btn btn-primary" onclick="saveBooking()">Создать бронирование</button>
                <button type="button" class="btn" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    `;
    
    showModal('Новое бронирование', content);
}

function updateAvailableRooms(hotelId) {
    const roomSelect = document.getElementById('room-select');
    const availableRooms = app.rooms.filter(room => 
        room.hotel_id == hotelId && room.status === 'available'
    );
    
    roomSelect.innerHTML = availableRooms.map(room => 
        `<option value="${room.id}">Комната ${room.room_number} - ${room.price_per_night} руб./ночь (вмещает: ${room.capacity})</option>`
    ).join('') || '<option value="">Нет доступных комнат</option>';
}

async function saveBooking() {
    try {
        const formData = FormUtils.getFormData('booking-form');
        
        // Конвертируем числовые поля
        formData.user_id = parseInt(formData.user_id);
        formData.hotel_id = parseInt(formData.hotel_id);
        formData.room_id = parseInt(formData.room_id);
        formData.number_of_guests = parseInt(formData.number_of_guests);
        
        await ApiClient.post('/bookings/', formData);
        UIUtils.showMessage('Бронирование успешно создано');
        closeModal();
        await app.loadBookings();
    } catch (error) {
        UIUtils.showMessage('Ошибка при создании бронирования', 'error');
    }
}

async function checkInBooking(bookingId) {
    try {
        await ApiClient.put(`/bookings/${bookingId}/check-in`);
        UIUtils.showMessage('Заезд успешно зарегистрирован');
        await app.loadBookings();
    } catch (error) {
        UIUtils.showMessage('Ошибка при регистрации заезда', 'error');
    }
}

async function checkOutBooking(bookingId) {
    try {
        await ApiClient.put(`/bookings/${bookingId}/check-out`);
        UIUtils.showMessage('Выезд успешно зарегистрирован');
        await app.loadBookings();
    } catch (error) {
        UIUtils.showMessage('Ошибка при регистрации выезда', 'error');
    }
}

async function cancelBooking(bookingId) {
    if (confirm('Вы уверены, что хотите отменить это бронирование?')) {
        try {
            await ApiClient.put(`/bookings/${bookingId}/cancel`);
            UIUtils.showMessage('Бронирование успешно отменено');
            await app.loadBookings();
        } catch (error) {
            UIUtils.showMessage('Ошибка при отмене бронирования', 'error');
        }
    }
}

async function searchRooms() {
    const city = document.getElementById('search-city').value;
    const checkin = document.getElementById('search-checkin').value;
    const checkout = document.getElementById('search-checkout').value;
    const guests = document.getElementById('search-guests').value;
    
    if (!city || !checkin || !checkout) {
        UIUtils.showMessage('Заполните все поля для поиска', 'error');
        return;
    }
    
    try {
        const params = new URLSearchParams({
            city: city,
            check_in: checkin,
            check_out: checkout,
            guests: guests
        });
        
        const results = await ApiClient.get(`/rooms/search/available?${params}`);
        displaySearchResults(results);
    } catch (error) {
        UIUtils.showMessage('Ошибка при поиске комнат', 'error');
    }
}

function displaySearchResults(rooms) {
    const container = document.getElementById('search-results');
    
    if (!rooms.length) {
        container.innerHTML = '<p>По вашему запросу ничего не найдено</p>';
        return;
    }
    
    container.innerHTML = rooms.map(room => {
        const hotel = app.hotels.find(h => h.id === room.hotel_id);
        
        return `
            <div class="card">
                <h3>Комната ${room.room_number}</h3>
                <p><strong>Отель:</strong> ${hotel?.name || 'Неизвестно'}</p>
                <p><strong>Адрес:</strong> ${hotel?.address || ''}, ${hotel?.city || ''}</p>
                <p><strong>Тип:</strong> ${room.room_type}</p>
                <p><strong>Цена за ночь:</strong> ${room.price_per_night} руб.</p>
                <p><strong>Вместимость:</strong> ${room.capacity} гостей</p>
                <p><strong>Этаж:</strong> ${room.floor}</p>
                ${room.description ? `<p><strong>Описание:</strong> ${room.description}</p>` : ''}
                ${room.amenities ? `<p><strong>Удобства:</strong> ${room.amenities}</p>` : ''}
                
                <div class="card-actions">
                    <button class="btn btn-primary" onclick="bookThisRoom(${room.id})">Забронировать</button>
                </div>
            </div>
        `;
    }).join('');
}

function bookThisRoom(roomId) {
    const room = app.rooms.find(r => r.id === roomId);
    if (room) {
        showBookingForm();
        setTimeout(() => {
            document.querySelector('select[name="hotel_id"]').value = room.hotel_id;
            updateAvailableRooms(room.hotel_id);
            setTimeout(() => {
                document.querySelector('select[name="room_id"]').value = roomId;
            }, 100);
        }, 100);
    }
}

async function deleteBooking(booking_id) {
    if (confirm('Вы уверены, что хотите удалить это бронирование?')) {
        try {
            await ApiClient.delete(`/bookings/${booking_id}`);
            UIUtils.showMessage('Бронирование успешно удалено');
            await app.loadBookings();
        } catch (error) {
            UIUtils.showMessage('Ошибка при удалении бронирования', 'error');
        }
    }
}