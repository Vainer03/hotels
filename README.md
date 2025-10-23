# 🏨 Hotel Booking System

Полнофункциональная система бронирования отелей с микросервисной архитектурой, построенная на FastAPI, PostgreSQL, Redis, RabbitMQ и Celery.

## 🚀 Возможности

- **Управление отелями** - CRUD операции для отелей
- **Управление комнатами** - создание, редактирование, поиск доступных комнат
- **Бронирование** - полный цикл бронирования с подтверждением
- **Пользователи** - управление гостями и их бронированиями
- **Поиск** - интеллектуальный поиск доступных комнат по критериям
- **Кэширование** - Redis для повышения производительности

## 🏗️ Архитектура

### Технологический стек

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| **Backend** | FastAPI + Python 3.11 | REST API |
| **Frontend** | Vanilla JS + HTML/CSS | Веб-интерфейс |
| **База данных** | PostgreSQL + SQLAlchemy | Основное хранилище |
| **Кэш** | Redis | Кэширование, сессии |
| **Очереди** | RabbitMQ + Celery | Асинхронные задачи |
| **Прокси** | Nginx | Балансировка, статика |
| **Контейнеризация** | Docker + Docker Compose | Развертывание |

### Микросервисы

- **`hotel-booking-api`** - FastAPI бэкенд
- **`hotel-booking-frontend`** - Веб-интерфейс
- **`hotel-booking-postgres`** - База данных PostgreSQL
- **`hotel-booking-redis`** - Кэш Redis
- **`hotel-booking-rabbitmq`** - Брокер сообщений
- **`hotel-booking-nginx`** - Прокси-сервер

## 📁 Структура проекта

```
hotels/
├── 🐳 Dockerfile                 # Backend образ
├── 📋 requirements.txt           # Python зависимости
├── 🐳 docker-compose.yml         # Оркестрация сервисов
│
├── 📁 nginx/                     # Прокси-сервер
│   ├── 🐳 Dockerfile
│   └── ⚙️ nginx.conf
│
├── 📁 app/                       # Backend приложение
│   ├── 🚀 main.py                # Точка входа
│   ├── 🗄️ database.py           # Настройка БД
│   ├── 📁 models/               # Модели данных
│   ├── 📁 schemas/              # Pydantic схемы
│   ├── 📁 routers/              # API эндпоинты
│   ├── 📁 core/                 # Ядро системы
│   ├── 📁 tasks/                # Фоновые задачи
│   └── 📁 services/             # Бизнес-логика
│
└── 📁 frontend/                 # Веб-интерфейс
    ├── 🏠 index.html
    ├── 🎨 css/style.css
    ├── ⚙️ nginx.conf
    └── 📁 js/                   # JavaScript модули
```

## 🛠️ Установка и запуск

### Предварительные требования

- Docker

### Быстрый старт

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
```

2. **Запустите систему**
```bash
docker-compose up --build -d
```

3. **Проверьте статус**
```bash
docker-compose ps
```

4. **Откройте приложение**
   - Frontend: http://localhost
   - API Docs: http://localhost/docs
   - RabbitMQ: http://localhost:15672 (guest/guest)

### Инициализация данных

```bash
# Создание тестовых данных
curl -X POST http://localhost/api/v1/tasks/init-mock-data
```

## 📚 API Документация

### Основные эндпоинты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/api/v1/hotels/` | Список отелей |
| `POST` | `/api/v1/hotels/` | Создать отель |
| `GET` | `/api/v1/rooms/available` | Поиск доступных комнат |
| `POST` | `/api/v1/bookings/` | Создать бронирование |
| `GET` | `/api/v1/users/{user_id}/bookings` | Бронирования пользователя |

### Примеры запросов

**Поиск доступных комнат:**
```bash
curl "http://localhost/api/v1/rooms/available?hotel_id=1&check_in_date=2024-01-15&check_out_date=2024-01-20"
```

**Создание бронирования:**
```bash
curl -X POST http://localhost/api/v1/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "hotel_id": 1,
    "room_id": 1,
    "check_in_date": "2024-01-15T14:00:00",
    "check_out_date": "2024-01-20T12:00:00",
    "number_of_guests": 2
  }'
```

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| `DATABASE_URL` | `postgresql://postgres:postgres@postgres:5432/hotel_booking` | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` | RabbitMQ connection string |

### Портs

| Сервис | Порт | Назначение |
|--------|------|------------|
| Nginx | 80 | Веб-интерфейс и API |
| PostgreSQL | 5432 | База данных |
| Redis | 6379 | Кэш |
| RabbitMQ | 5672 | Сообщения |
| RabbitMQ Management | 15672 | Веб-интерфейс |

## 🎯 Использование

### Управление отелями

1. Откройте http://localhost
2. Перейдите в раздел "Отели"
3. Создайте новый отель с указанием названия, адреса, города

### Бронирование комнаты

1. Найдите доступные комнаты через раздел "Поиск"
2. Выберите даты заезда/выезда
3. Забронируйте подходящую комнату
4. Получите подтверждение по email

### Мониторинг системы

- **Health Check**: http://localhost/health
- **Статистика кэша**: http://localhost/api/v1/tasks/cache/stats
- **Статус задач**: http://localhost/api/v1/tasks/status/{task_id}

## 🔄 Фоновые задачи

Система использует Celery для асинхронной обработки:

- **Отправка email** - подтверждения бронирований
- **Генерация отчетов** - аналитика и статистика
- **Очистка данных** - обслуживание базы данных
