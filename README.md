# Python API Домашняя работа 3
# 1. Описание API
Сервер поднял локально скрин экрана приложил![Localhost](https://github.com/user-attachments/assets/0d516a09-5ae2-4d7f-826b-93f2a53a9ba1)
Деплой на сайте render.com. приложение по ссылке: https://python-hw3.onrender.com ![rendercom](https://github.com/user-attachments/assets/e6689412-c37c-4016-b3ef-00d212eeb7b5)


# 2. Краткое описание структуры базы данных и методов работы с ней
Структура базы данных
## Таблица users – хранит информацию о пользователях:
- id – идентификатор пользователя (SERIAL PRIMARY KEY).
- auth_token – токен пользователя (TEXT NOT NULL).
## Таблица links – хранит данные о коротких ссылках:
- id – идентификатор ссылки (SERIAL PRIMARY KEY).
- client_id – идентификатор пользователя (INTEGER).
- long_link – оригинальная ссылка (VARCHAR(255) NOT NULL).
- short_link – короткая ссылка (VARCHAR(255) NOT NULL).
- created_at – дата создания (TIMESTAMP DEFAULT CURRENT_TIMESTAMP).
- expires_at – дата истечения (TIMESTAMP).
- sign_up_create_account – флаг авторизованного пользователя (BOOLEAN DEFAULT FALSE).
## Таблица statistics – хранит статистику переходов по ссылкам:
- id – идентификатор записи (SERIAL PRIMARY KEY).
- short_link – короткая ссылка (VARCHAR(255) NOT NULL).
- access_date – дата доступа (TIMESTAMP DEFAULT CURRENT_TIMESTAMP).
## Таблица expired_links – хранит просроченные ссылки:
- id – идентификатор (SERIAL PRIMARY KEY).
- client_id – идентификатор пользователя (INTEGER).
- long_link – полная ссылка (VARCHAR(255) NOT NULL).
- short_link – короткая ссылка (VARCHAR(255) NOT NULL).
- created_at – дата создания (TIMESTAMP).
- expires_at – дата истечения (TIMESTAMP).
- deleted_at – дата удаления (TIMESTAMP DEFAULT CURRENT_TIMESTAMP).
- sign_up_create_account – флаг авторизованного пользователя (BOOLEAN DEFAULT FALSE).
## Основные методы работы с БД
## Регистрация и проверка пользователей
- get_user_by_credentials(client_id, auth_token): проверка пользователя по ID и токену.
## Работа с короткими ссылками
- store_link(long_link, short_link, client_id, is_authorized, expires_at): создание ссылки.
- search_at_the_source_url_short_link(short_url): получение оригинальной ссылки по короткому идентификатору.
- client_created_shortcut(short_url): получение ID пользователя, создавшего ссылку.
- removes_short_reference_database(short_url): удаление короткой ссылки.
- method_updates_source_link(short_link, long_link): обновление оригинальной ссылки.
- return_date_created_short_link(short_link): получение даты создания короткой ссылки.
## Статистика и аналитика
- saves_short_link_access_statistics_table(short_url): сохранение информации о переходе.
- return_statistics_short_link(short_url): получение статистики (количество переходов, последнее использование).
- alias_availability_check(alias): проверка доступности алиаса.
- search_short_link_at_the_source_url(original_url): поиск короткой ссылки по оригинальной.
## Очистка и управление ссылками
- purge_old_links(): перемещение просроченных ссылок в архив.
- return_all_links_users(client_id): получение количества активных и просроченных ссылок.
- pool_database_connection_close(): закрытие соединения с БД.

  # Домашняя работа 4 (тесты)
- Юнит-тесты (tests/unit/)
-- test_business_logic.py
-- test_interact_postgres.py
- Функциональные тесты (tests/functional/)
-- conftest.py
-- test_api.py
- Нагрузочное тестирование
  --locustfile.py

- requirements-test.txt

- запуск тестов: ![Test](https://github.com/user-attachments/assets/f2399f9a-52fb-4dc6-beed-1b2bb8f76aae)

