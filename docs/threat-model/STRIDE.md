# STRIDE Threat Analysis

## Media Catalog API - Анализ угроз по методологии STRIDE

### Методология STRIDE

**STRIDE** - модель классификации угроз по 6 категориям:

- **S**poofing (Подмена) - притворство кем-то другим
- **T**ampering (Вмешательство) - изменение данных/кода
- **R**epudiation (Отказ) - отрицание совершенных действий
- **I**nformation Disclosure (Раскрытие информации) - доступ к конфиденциальным данным
- **D**enial of Service (Отказ в обслуживании) - нарушение доступности
- **E**levation of Privilege (Повышение привилегий) - получение несанкционированных прав

### STRIDE Analysis для Media Catalog

| Поток/Элемент | Угроза | STRIDE | Сценарий атаки | Контроль | NFR | Статус | Проверка |
|---------------|--------|--------|----------------|----------|-----|--------|----------|
| **F1: User → API** | Подмена пользователя | **S** | Атакующий использует чужие учетные данные для доступа к медиа другого пользователя | Аутентификация + user_id изоляция | NFR-06 | Частично | [`tests/test_media.py`][`tests/test_media.py`](tests/test_media.py ) строки 180-200 |
| **F1: User → API** | HTTP Injection атаки | **T** | Инъекция в JSON payload: `{"title": "<script>alert('xss')</script>"}` | Input validation с Pydantic | NFR-03 | Реализовано | [`tests/test_media.py`][`tests/test_media.py`](tests/test_media.py ) строки 290-320 |
| **F3: API Requests** | DoS через большие запросы | **D** | Отправка JSON payload > 100MB для исчерпания памяти | Request size limiting | NFR-07 | Не реализовано | Issue #12 |
| **F3: API Requests** | DoS через высокую частоту | **D** | 1000+ запросов/сек для перегрузки сервера | Rate limiting middleware | NFR-08 | Не реализовано | Issue #12 |
| **F4: API → MemDB** | SQL Injection (подготовка) | **T** | `'; DROP TABLE media; --` в поле title | SAST сканирование bandit | NFR-04 | Частично | Issue #10 - добавить bandit |
| **F4: API → MemDB** | Межпользовательский доступ | **E** | Доступ к медиа другого пользователя через прямой ID | Data isolation с user_id фильтрацией | NFR-06 | Реализовано | [`app/crud/media.py`][`app/crud/media.py`](app/crud/media.py ) все функции |
| **F5: API → Logs** | Log injection | **T** | Вставка `\n[FAKE LOG ENTRY]` через user input | Log sanitization + structured logging | NFR-09 | Не реализовано | Issue #13 |
| **F5: API → Logs** | Отсутствие аудита действий | **R** | Пользователь отрицает удаление медиа - нет доказательств | Audit logging всех CRUD операций | NFR-09 | Не реализовано | Issue #13 |
| **F6: API → Config** | Раскрытие секретов в коде | **I** | Хардкод API ключей в исходном коде | Secret detection в pre-commit | NFR-10 | Частично | [`.pre-commit-config.yaml`][`.pre-commit-config.yaml`](.pre-commit-config.yaml ) - добавить detect-secrets |
| **F1-F3: Error Responses** | Information disclosure через ошибки | **I** | `"Media with id 123 not found"` раскрывает валидные ID | Безопасные error messages | NFR-13 | Частично | Issue #15 - исправить [`app/api/media.py`][`app/api/media.py`](app/api/media.py ) строки 45, 85, 115 |
| **F1-F3: Content-Type** | Content-Type confusion | **T** | Отправка XML/HTML вместо JSON для обхода валидации | Strict Content-Type validation | NFR-11 | Не реализовано | Issue #14 |
| **F10: Dependencies** | Уязвимые зависимости | **E** | Эксплуатация известных CVE в FastAPI/Pydantic | Dependency vulnerability scanning | NFR-05 | Не реализовано | Issue #10 - добавить safety |
| **F1-F3: Performance** | Slowloris DoS | **D** | Медленные запросы для исчерпания connection pool | Response time monitoring + timeouts | NFR-01, NFR-02 | Не реализовано | Issue #7, #8 |

### Исключенные угрозы (не применимо)

| STRIDE | Угроза | Обоснование исключения |
|--------|--------|------------------------|
| **S: Spoofing Services** | Подмена FastAPI сервиса | Нет распределенной архитектуры, монолитное приложение |
| **T: Code Tampering** | Изменение исходного кода | Защищено Git + GitHub branch protection |
| **R: Transaction Repudiation** | Отрицание транзакций | Нет финансовых операций в Media Catalog |
| **I: Memory Dumps** | Анализ дампов памяти | Нет чувствительных данных в памяти (только медиа каталог) |
| **E: OS Privilege Escalation** | Повышение прав в ОС | Вне scope приложения, ответственность платформы |

### Приоритизация угроз

#### 🔴 Критические (немедленно)

1. **F4: Data Isolation breach** (NFR-06) - ✅ **УЖЕ РЕАЛИЗОВАНО**
2. **F1-F3: Input validation bypass** (NFR-03) - ✅ **УЖЕ РЕАЛИЗОВАНО**
3. **F1-F3: Information disclosure** (NFR-13) - 🔄 **В ПРОЦЕССЕ** (Issue #15)

#### 🟡 Высокие (до 2025.11)

1. **F3: DoS через большие запросы** (NFR-07) - Issue #12
2. **F3: DoS через высокую частоту** (NFR-08) - Issue #12
3. **F4: SQL Injection protection** (NFR-04) - Issue #10
4. **F10: Уязвимые зависимости** (NFR-05) - Issue #10

#### 🟢 Средние (до 2025.12)

1. **F5: Log injection** (NFR-09) - Issue #13
2. **F5: Отсутствие аудита** (NFR-09) - Issue #13
3. **F1-F3: Content-Type confusion** (NFR-11) - Issue #14
4. **F6: Раскрытие секретов** (NFR-10) - Issue #10
5. **F1-F3: Performance DoS** (NFR-01, NFR-02) - Issue #7, #8

### Связь с GitHub Issues

| STRIDE Угрозы | GitHub Issue | Milestone | Исполнитель |
|---------------|--------------|-----------|----------|
| S,E: Authentication & Data Isolation | [#11](https://github.com/DedovInside/course-project/issues/11) ✅ | 2025.10 (Done) | @DedovInside |
| T: Input Validation | [#9](https://github.com/DedovInside/course-project/issues/9) ✅ | 2025.10 (Done) | @DedovInside |
| T,E: SAST & Dependencies | [#10](https://github.com/DedovInside/course-project/issues/10) | 2025.10 (Active) | @DedovInside |
| D: DoS Protection | [#12](https://github.com/DedovInside/course-project/issues/12) | 2025.11 | @DedovInside |
| R,T: Audit Logging | [#13](https://github.com/DedovInside/course-project/issues/13) | 2025.11 | @DedovInside |
| T: Content-Type Validation | [#14](https://github.com/DedovInside/course-project/issues/14) | 2025.11 | @DedovInside |
| I: Error Response Security | [#15](https://github.com/DedovInside/course-project/issues/15) | 2025.10 (Active) | @DedovInside |
