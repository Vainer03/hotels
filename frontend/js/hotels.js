function showHotelForm(hotel = null) {
    const isEdit = !!hotel;
    const title = isEdit ? 'Редактировать отель' : 'Добавить отель';
    
    const content = `
        <form id="hotel-form">
            <div class="form-group">
                <label>Название отеля:</label>
                <input type="text" name="name" value="${hotel?.name || ''}" required>
            </div>
            <div class="form-group">
                <label>Описание:</label>
                <textarea name="description">${hotel?.description || ''}</textarea>
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
                <input type="number" name="rating" step="0.1" min="0" max="5" value="${hotel?.rating || 0}">
            </div>
            <div class="card-actions">
                <button type="button" class="btn btn-primary" onclick="saveHotel(${hotel?.id || null})">
                    ${isEdit ? 'Обновить' : 'Создать'}
                </button>
                <button type="button" class="btn" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    `;
    
    showModal(title, content);
}

async function saveHotel(hotelId = null) {
    try {
        const formData = FormUtils.getFormData('hotel-form');
        
        formData.rating = parseFloat(formData.rating);
        
        let response;
        if (hotelId) {
            response = await ApiClient.put(`/hotels/${hotelId}`, formData);
            UIUtils.showMessage('Отель успешно обновлен');
        } else {
            response = await ApiClient.post('/hotels/', formData);
            UIUtils.showMessage('Отель успешно создан');
        }
        
        closeModal();
        
        await app.loadHotels();
        
    } catch (error) {
        console.error('Error saving hotel:', error);
        console.error('Error details:', error.message);
        UIUtils.showMessage('Ошибка при сохранении отеля: ' + error.message, 'error');
    }
}

async function editHotel(hotelId) {
    const hotel = app.hotels.find(h => h.id === hotelId);
    if (hotel) {
        showHotelForm(hotel);
    }
}

async function deleteHotel(hotelId) {
    if (confirm('Вы уверены, что хотите удалить этот отель?')) {
        try {
            await ApiClient.delete(`/hotels/${hotelId}`);
            UIUtils.showMessage('Отель успешно удален');
            await app.loadHotels();
        } catch (error) {
            UIUtils.showMessage('Ошибка при удалении отеля', 'error');
        }
    }
}