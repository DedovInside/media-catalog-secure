# NFR Traceability Matrix

## Media Catalog API - NFR to User Stories Mapping

### User Stories Overview

**Основные пользовательские истории Media Catalog:**

- **MC-01**: Как пользователь, я хочу добавлять медиа в каталог
- **MC-02**: Как пользователь, я хочу просматривать список своих медиа
- **MC-03**: Как пользователь, я хочу обновлять информацию о медиа
- **MC-04**: Как пользователь, я хочу удалять медиа из каталога
- **MC-05**: Как пользователь, я хочу фильтровать медиа по типу и статусу
- **MC-06**: Как пользователь, я хочу изменять статус просмотра и ставить оценки
- **MC-07**: Как администратор, я хочу мониторить производительность системы
- **MC-08**: Как разработчик, я хочу безопасно развертывать обновления

### Трассировка NFR <-> User Stories

| NFR ID | Story ID | Story Name                    | Связь с NFR                              | Приоритет | Release/Milestone | Assignee | Status | GitHub Issue |
|--------|----------|-------------------------------|------------------------------------------|-----------|-------------------|----------|--------|--------------|
| NFR-01 | MC-02    | Просмотр списка медиа        | Производительность GET /media            | High      | 2025.11          | @DedovInside | Planned | [#7](https://github.com/DedovInside/course-project/issues/7) |
| NFR-01 | MC-05    | Фильтрация медиа             | Производительность с фильтрами           | High      | 2025.11          | @DedovInside | Planned | [#7](https://github.com/DedovInside/course-project/issues/7) |
| NFR-02 | MC-01    | Добавление медиа             | Мониторинг ошибок POST /media            | High      | 2025.10          | @DedovInside | Active  | [#8](https://github.com/DedovInside/course-project/issues/2) |
| NFR-02 | MC-07    | Мониторинг системы           | Метрики ошибок для dashboard             | High      | 2025.11          | @DedovInside | Planned | [#8](https://github.com/DedovInside/course-project/issues/8) |
| NFR-03 | MC-01    | Добавление медиа             | Валидация создания медиа                 | Critical  | 2025.10          | @DedovInside | Done | [#9](https://github.com/DedovInside/course-project/issues/9) |
| NFR-03 | MC-03    | Обновление медиа             | Валидация при обновлении                 | Critical  | 2025.10          | @DedovInside | Done | [#9](https://github.com/DedovInside/course-project/issues/9) |
| NFR-03 | MC-06    | Изменение статуса            | Валидация rating (1-10)                  | Critical  | 2025.10          | @DedovInside | Done | [#9](https://github.com/DedovInside/course-project/issues/9) |
| NFR-04 | MC-08    | Безопасное развертывание     | SAST в CI/CD pipeline                    | Critical  | 2025.10          | @DedovInside | In Progress | [#10](https://github.com/DedovInside/course-project/issues/10) |
| NFR-05 | MC-08    | Безопасное развертывание     | Контроль уязвимостей зависимостей        | High      | 2025.10          | @DedovInside | In Progress | [#10](https://github.com/DedovInside/course-project/issues/10) |
| NFR-06 | MC-02    | Просмотр списка медиа        | Изоляция данных пользователей            | Critical  | 2025.10          | @DedovInside | Done | [#11](https://github.com/DedovInside/course-project/issues/11) |
| NFR-06 | MC-03    | Обновление медиа             | Доступ только к собственным медиа        | Critical  | 2025.10          | @DedovInside | Done | [#11](https://github.com/DedovInside/course-project/issues/11) |
| NFR-06 | MC-04    | Удаление медиа               | Защита от удаления чужих медиа           | Critical  | 2025.10          | @DedovInside | Done | [#11](https://github.com/DedovInside/course-project/issues/11) |
| NFR-06 | MC-06    | Изменение статуса            | user_id фильтрация при обновлении        | Critical  | 2025.10          | @DedovInside | Done | [#11](https://github.com/DedovInside/course-project/issues/11) |
| NFR-07 | MC-01    | Добавление медиа             | Защита от больших payload                | Medium    | 2025.11          | @DedovInside | Not Started | [#12](https://github.com/DedovInside/course-project/issues/12) |
| NFR-08 | MC-07    | Мониторинг системы           | Rate limiting для защиты                 | Medium    | 2025.11          | @DedovInside | Not Started | [#12](https://github.com/DedovInside/course-project/issues/12) |
| NFR-09 | MC-01    | Добавление медиа             | Аудит создания медиа                     | Medium    | 2025.11          | @DedovInside | Not Started | [#13](https://github.com/DedovInside/course-project/issues/13) |
| NFR-09 | MC-03    | Обновление медиа             | Аудит изменений медиа                    | Medium    | 2025.11          | @DedovInside | Not Started | [#13](https://github.com/DedovInside/course-project/issues/13) |
| NFR-09 | MC-04    | Удаление медиа               | Аудит удаления медиа                     | Medium    | 2025.11          | @DedovInside | Not Started | [#13](https://github.com/DedovInside/course-project/issues/13) |
| NFR-10 | MC-08    | Безопасное развертывание     | Secret management в конфигурации         | High      | 2025.10          | @DedovInside | In Progress | [#10](https://github.com/DedovInside/course-project/issues/10) |
| NFR-11 | MC-01    | Добавление медиа             | Content-Type валидация для POST          | Medium    | 2025.11          | @DedovInside | Not Started | [#14](https://github.com/DedovInside/course-project/issues/14) |
| NFR-11 | MC-03    | Обновление медиа             | Content-Type валидация для PUT           | Medium    | 2025.11          | @DedovInside | Not Started | [#14](https://github.com/DedovInside/course-project/issues/14) |
| NFR-13 | MC-01    | Добавление медиа             | Безопасные error responses               | High      | 2025.10          | @DedovInside | In Progress | [#15](https://github.com/DedovInside/course-project/issues/15) |
| NFR-13 | MC-02    | Просмотр списка медиа        | Information disclosure prevention        | High      | 2025.10          | @DedovInside | In Progress | [#15](https://github.com/DedovInside/course-project/issues/15) |

#### Milestone: (2025.10) - Critical Security Foundation

**Status:** In Progress

- **NFR-03**: Покрытие валидации входных данных (Critical) - **DONE**
- **NFR-06**: Изоляция данных между пользователями (Critical) - **DONE**
- **NFR-04**: Защита от SQL инъекций (подготовка к БД) (Critical) - **IN PROGRESS**
- **NFR-05**: Контроль уязвимостей в зависимостях (High) - **IN PROGRESS**
- **NFR-10**: Безопасное хранение конфигурации (High) - **IN PROGRESS**
- **NFR-13**: Безопасные тела ошибок согласно SECURITY.md. (High) - **IN PROGRESS**

#### Milestone: (2025.11) - Performance & Observability

**Status:** Planned

- **NFR-01**: Время отклика API эндпоинтов под нагрузкой (High)
- **NFR-02**: Максимальный процент ошибок API (High)
- **NFR-07**: Ограничение размера HTTP запросов (Medium)
- **NFR-08**: Защита от DDoS и злоупотреблений (Medium)
- **NFR-09**: Логирование критических операций (Medium)
- **NFR-11**: Строгая проверка Content-Type заголовков (Medium)

### Текущий статус реализации и CI доказательства

#### Уже реализованные и проверенные (критерий C5 P03)

#### NFR-03: Input Validation Coverage

```python
# EVIDENCE: tests/test_media.py - 17 automated tests
class TestMediaValidation:
    def test_create_media_invalid_year_future(self):
        response = client.post("/media", json={"year": 2050})
        assert response.status_code == 422  # VALIDATION WORKS

    def test_create_media_empty_title(self):
        response = client.post("/media", json={"title": ""})
        assert response.status_code == 422  # VALIDATION WORKS

# CI EVIDENCE: .github/workflows/ci.yml
- name: Tests
  run: pytest -q  # ALL TESTS PASS IN CI
```

#### NFR-06: Data Isolation

```python
# EVIDENCE: app/crud/media.py - user_id filtering everywhere
def get_media_list(user_id: int, kind=None, status=None) -> List[Media]:
    media_list = [media for media in _MEDIA_DB if media.user_id == user_id]  # ISOLATION

def get_media_by_id(media_id: int, user_id: int) -> Optional[Media]:
    for media in _MEDIA_DB:
        if media.id == media_id and media.user_id == user_id:  # OWNER CHECK
            return media

# CI EVIDENCE: tests/test_media.py - integration tests verify isolation
def test_full_media_lifecycle(self):
    # ALL CRUD OPERATIONS VERIFIED WITH USER_ID FILTERING
```

### Задачи по реализации (критерий C4 доказательства)

Все расписаны в Issues.
