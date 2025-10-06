# Security Non-Functional Requirements (NFR)

## Media Catalog API - Security NFR Specification

### Описание проекта

**Media Catalog** - персональный каталог медиа контента (фильмы, сериалы, курсы) с REST API для управления списком "к просмотру".

### Security NFR Requirements

| ID     | Название                    | Описание                                           | Метрика/Порог                    | Проверка (чем/где)                      | Компонент    | Приоритет |
|--------|-----------------------------|----------------------------------------------------|---------------------------------|------------------------------------------|--------------|-----------|
| NFR-01 | API Response Time          | Время отклика API эндпоинтов под нагрузкой        | p95 ≤ 200ms при 100 RPS        | Нагрузочное тестирование (pytest-benchmark) | api/media    | High      |
| NFR-02 | Error Rate Threshold       | Максимальный процент ошибок API                   | ≤ 1% ошибок 5xx за час          | CI метрики + мониторинг логов            | api          | High      |
| NFR-03 | Input Validation Coverage  | Покрытие валидации входных данных                  | 100% эндпоинтов с валидацией    | Unit тесты + контракт тесты              | schemas      | Critical  |
| NFR-04 | SQL Injection Protection   | Защита от SQL инъекций (подготовка к БД)          | 0 уязвимостей в коде            | SAST сканирование (bandit)               | crud         | Critical  |
| NFR-05 | Dependency Vulnerabilities | Контроль уязвимостей в зависимостях               | High/Critical ≤ 3 дня           | safety + pip-audit в CI                  | requirements | High      |
| NFR-06 | Data Isolation             | Изоляция данных между пользователями              | 100% запросов с user_id фильтром| Integration тесты + code review          | crud/media   | Critical  |
| NFR-07 | Request Size Limits        | Ограничение размера HTTP запросов                 | ≤ 1MB на запрос                | FastAPI настройки + тесты                | api          | Medium    |
| NFR-08 | Rate Limiting              | Защита от DDoS и злоупотреблений                 | ≤ 100 req/min на IP             | Middleware + тестирование                | api          | Medium    |
| NFR-09 | Audit Logging              | Логирование критических операций                  | 100% CRUD операций логируются   | Structured logging + тесты               | crud         | Medium    |
| NFR-10 | Secret Management          | Безопасное хранение конфигурации                  | Нет секретов в коде/логах       | pre-commit hooks (detect-secrets)        | config       | High      |
| NFR-11 | Content-Type Validation    | Строгая проверка Content-Type заголовков          | Только application/json принимается | API тесты + security тесты            | api          | Medium    |
| NFR-12 | Error Response Security    | Безопасные тела ошибок согласно SECURITY.md. Предотвращение information disclosure | 0% sensitive data в error responses | Security code review + automated tests | api | High |

### Future NFR (для следующих релизов)

**Эти NFR станут актуальными при добавлении аутентификации:**

| ID     | Название                    | Описание                                           | Метрика/Порог                    | Компонент | Приоритет |
|--------|-----------------------------|----------------------------------------------------|---------------------------------|-----------|-----------|
| NFR-F1 | Password Hashing           | Хэширование паролей только Argon2id                | t=3, m=256MB, p=1              | auth      | High      |
| NFR-F2 | Login Performance          | p95 ≤ 300ms для /login при 50 RPS                 | p95 ≤ 300ms @ 50 RPS           | auth      | High      |
| NFR-F3 | Session Management         | TTL сессий и безопасная ротация                    | Max 24h TTL, auto-refresh      | auth      | Medium    |
| NFR-F4 | Secrets Rotation           | Автоматическая ротация JWT ключей                  | Каждые 30 дней                | platform  | Medium    |
