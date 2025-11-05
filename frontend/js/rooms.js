function renderRooms() {
    const container = document.getElementById('rooms-list');
    
    if (!app.rooms.length) {
        container.innerHTML = '<p>Комнаты не найдены</p>';
        return;
    }

    container.innerHTML = app.rooms.map(room => {
        const hotel = app.hotels.find(h => h.id === room.hotel_id);
        const statusClass = UIUtils.getRoomStatusClass(room.status);
        
        return `
            <div class="card">
                <h3>Комната ${room.room_number}</h3>
                <p><strong>Отель:</strong> ${hotel?.name || 'Неизвестно'}</p>
                <p><strong>Этаж:</strong> ${room.floor}</p>
                <p><strong>Тип:</strong> ${room.room_type}</p>
                <p><strong>Цена за ночь:</strong> ${room.price_per_night} руб.</p>
                <p><strong>Вместимость:</strong> ${room.capacity} гостей</p>
                <p><strong>Статус:</strong> <span class="${statusClass}">${getRoomStatusText(room.status)}</span></p>
                ${room.description ? `<p><strong>Описание:</strong> ${room.description}</p>` : ''}
                ${room.amenities ? `<p><strong>Удобства:</strong> ${room.amenities}</p>` : ''}
                
                <div class="card-actions">
                    <button class="btn btn-warning" onclick="editRoom(${room.id})">Редактировать</button>
                    <button class="btn btn-danger" onclick="deleteRoom(${room.id})">Удалить</button>
                    <button class="btn" onclick="updateRoomStatus(${room.id})">Изменить статус</button>
                </div>
            </div>
        `;
    }).join('');
}

function getRoomStatusText(status) {
    const statusMap = {
        'available': 'Доступна',
        'occupied': 'Занята',
        'maintenance': 'На обслуживании',
        'cleaning': 'Уборка'
    };
    return statusMap[status] || status;
}

function showRoomForm(room = null) {
    const isEdit = !!room;
    const title = isEdit ? 'Редактировать комнату' : 'Добавить комнату';
    
    const hotelsOptions = app.hotels.map(hotel => 
        `<option value="${hotel.id}" ${room?.hotel_id === hotel.id ? 'selected' : ''}>${hotel.name}</option>`
    ).join('');
    
    const content = `
        <form id="room-form">
            <div class="form-group">
                <label>Отель:</label>
                <select name="hotel_id" required>
                    <option value="">Выберите отель</option>
                    ${hotelsOptions}
                </select>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Номер комнаты:</label>
                    <input type="text" name="room_number" value="${room?.room_number || ''}" required>
                </div>
                <div class="form-group">
                    <label>Этаж:</label>
                    <input type="number" name="floor" value="${room?.floor || 1}" min="1" required>
                </div>
            </div>
            <div class="form-group">
                <label>Тип комнаты:</label>
                <input type="text" name="room_type" value="${room?.room_type || ''}" required>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Цена за ночь:</label>
                    <input type="number" name="price_per_night" step="0.01" value="${room?.price_per_night || ''}" required>
                </div>
                <div class="form-group">
                    <label>Вместимость:</label>
                    <input type="number" name="capacity" value="${room?.capacity || 2}" min="1" required>
                </div>
            </div>
            <div class="form-group">
                <label>Статус:</label>
                <select name="status">
                    <option value="available" ${room?.status === 'available' ? 'selected' : ''}>Доступна</option>
                    <option value="occupied" ${room?.status === 'occupied' ? 'selected' : ''}>Занята</option>
                    <option value="maintenance" ${room?.status === 'maintenance' ? 'selected' : ''}>На обслуживании</option>
                    <option value="cleaning" ${room?.status === 'cleaning' ? 'selected' : ''}>Уборка</option>
                </select>
            </div>
            <div class="form-group">
                <label>Описание:</label>
                <textarea name="description">${room?.description || ''}</textarea>
            </div>
            <div class="form-group">
                <label>Удобства:</label>
                <textarea name="amenities" placeholder="WiFi, TV, Кондиционер...">${room?.amenities || ''}</textarea>
            </div>
            <div class="card-actions">
                <button type="button" class="btn btn-primary" onclick="saveRoom(${room?.id || null})">
                    ${isEdit ? 'Обновить' : 'Создать'}
                </button>
                <button type="button" class="btn" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    `;
    
    showModal(title, content);
}

async function saveRoom(roomId = null) {
    try {
        const formData = FormUtils.getFormData('room-form');
        
        formData.floor = parseInt(formData.floor);
        formData.price_per_night = parseFloat(formData.price_per_night);
        formData.capacity = parseInt(formData.capacity);
        formData.hotel_id = parseInt(formData.hotel_id);
        
        if (roomId) {
            await ApiClient.put(`/rooms/${roomId}`, formData);
            UIUtils.showMessage('Комната успешно обновлена');
        } else {
            await ApiClient.post('/rooms/', formData);
            UIUtils.showMessage('Комната успешно создана');
        }
        
        closeModal();
        await app.loadRooms();
    } catch (error) {
        UIUtils.showMessage('Ошибка при сохранении комнаты', 'error');
    }
}

async function editRoom(roomId) {
    const room = app.rooms.find(r => r.id === roomId);
    if (room) {
        showRoomForm(room);
    }
}

async function deleteRoom(roomId) {
    if (confirm('Вы уверены, что хотите удалить эту комнату?')) {
        try {
            await ApiClient.delete(`/rooms/${roomId}`);
            UIUtils.showMessage('Комната успешно удалена');
            await app.loadRooms();
        } catch (error) {
            UIUtils.showMessage('Ошибка при удалении комнаты', 'error');
        }
    }
}

async function updateRoomStatus(roomId) {
    const room = app.rooms.find(r => r.id === roomId);
    if (!room) return;
    
    const content = `
        <form id="status-form">
            <div class="form-group">
                <label>Новый статус:</label>
                <select name="status">
                    <option value="available" ${room.status === 'available' ? 'selected' : ''}>Доступна</option>
                    <option value="occupied" ${room.status === 'occupied' ? 'selected' : ''}>Занята</option>
                    <option value="maintenance" ${room.status === 'maintenance' ? 'selected' : ''}>На обслуживании</option>
                    <option value="cleaning" ${room.status === 'cleaning' ? 'selected' : ''}>Уборка</option>
                </select>
            </div>
            <div class="card-actions">
                <button type="button" class="btn btn-primary" onclick="saveRoomStatus(${roomId})">Обновить статус</button>
                <button type="button" class="btn" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    `;
    
    showModal('Изменить статус комнаты', content);
}

async function saveRoomStatus(roomId) {
    try {
        const formData = FormUtils.getFormData('status-form');
        await ApiClient.put(`/rooms/${roomId}/status`, formData);
        UIUtils.showMessage('Статус комнаты обновлен');
        closeModal();
        await app.loadRooms();
    } catch (error) {
        UIUtils.showMessage('Ошибка при обновлении статуса', 'error');
    }
}