# ADR-001: Error Response Security (RFC 7807)

**Дата:** 2025-10-18
**Статус:** Accepted
**Решение по:** Information Disclosure через error messages

## Context

### Проблема

В текущей реализации Media Catalog API error responses раскрывают чувствительную информацию:

```python
# app/api/media.py - текущие проблемы:
raise ApiError(
    code="not_found",
    message=f"Media with id {media_id} not found",  # Раскрывает ID
    status=404
)

raise ApiError(
    code="media_already_exists",
    message=f"Media '{media_data.title}' ({media_data.year}) already exists"  # Раскрывает данные
)
```

### Security Impact

- **Information Enumeration**: Атакующие могут узнать валидные media IDs
- **Data Harvesting**: Раскрытие названий и годов существующих медиа
- **User Privacy**: Возможность определить предпочтения других пользователей

### Compliance Требования

- **OWASP Top 10**: A01 - Broken Access Control
- **P04 Threat Model**: R05 (L=3, I=4, Risk=12)
- **NFR-13**: 0% sensitive data в error responses

## Decision

### Принятое решение: RFC 7807 Problem Details

Реализуем стандартизированные error responses по RFC 7807 с:

1. **Унифицированная структура**:

```json
{
  "type": "https://example.com/probs/resource-not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "The requested resource could not be found",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

1. **Безопасные сообщения**:

- Generic messages без sensitive data
- correlation_id для internal debugging
- Structured error codes для programmatic handling

1. **Error mapping**:

```python
ERROR_MESSAGES = {
    "not_found": "The requested resource could not be found",
    "already_exists": "A resource with these properties already exists",
    "validation_error": "The provided data is invalid",
    "unauthorized": "Authentication required",
    "forbidden": "Access to this resource is not allowed"
}
```

## Alternatives

### Alternative 1: Оставить текущую систему

**Плюсы**: Нет дополнительной работы, детальные сообщения для debugging
**Минусы**: Security vulnerabilities, information disclosure, OWASP violations
**Вердикт**: Неприемлемо для production

### Alternative 2: Полностью generic ошибки

**Плюсы**: Максимальная безопасность
**Минусы**: Плохой DX, сложный debugging, нарушение HTTP semantics
**Вердикт**: Слишком радикально

### Alternative 3: Custom error format (не RFC 7807)

**Плюсы**: Полный контроль над структурой
**Минусы**: Reinventing the wheel, нет стандартизации, сложность поддержки
**Вердикт**: RFC 7807 уже решает наши задачи

## Consequences

### Положительные

- **Security**: Устранение information disclosure (закрывает R05)
- **Standardization**: RFC 7807 - industry standard
- **Debugging**: correlation_id для внутренней диагностики
- **API Consistency**: Единообразные error responses
- **Client Integration**: Предсказуемая структура для клиентов

### Отрицательные

- **Development Overhead**: Дополнительный код для error mapping
- **Debugging Complexity**: Нужно correlation_id для трассировки
- **Migration**: Обновление всех существующих error responses

### Компромиссы

- **Security vs Debugging**: Жертвуем детальными сообщениями ради безопасности
- **Standardization vs Control**: Используем RFC 7807 вместо custom format

## Security Impact (Summary)

### Устраняемые угрозы

- **STRIDE: Information Disclosure** в потоках F1-F3
- **Data Enumeration** через error messages
- **Privacy Violations** через раскрытие user data

### Новые риски

- **Log Injection** через correlation_id (митигация: UUID format)
- **Error Suppression** - важные детали могут потеряться (митигация: structured logging)

## Rollout Plan

### Фаза 1: Infrastructure (Week 1)

1. Создать `app/api/problem.py` с RFC 7807 utilities
2. Обновить `error_handlers.py` для support RFC 7807
3. Добавить error mapping dictionary

### Фаза 2: Implementation (Week 2)

1. Обновить все `raise ApiError()` calls в `app/api/media.py`
2. Обновить tests для ожидания RFC 7807 format
3. Добавить negative security tests

### Фаза 3: Validation (Week 3)

1. Contract tests для RFC 7807 compliance
2. Security testing для information disclosure
3. Performance testing (error responses не должны быть медленными)

### Definition of Done

- [ ] Все error responses следуют RFC 7807 format
- [ ] 0% sensitive data в error messages (verified by security tests)
- [ ] correlation_id в каждом error response
- [ ] Tests покрывают все error scenarios
- [ ] Documentation обновлена

## Links

### P03 Security NFR

- **NFR-12**: Безопасные error responses - **РЕАЛИЗУЕТ**

### P04 Threat Model

- **R05**: Information disclosure через ошибки (L=3, I=4, Risk=12) - **ЗАКРЫВАЕТ**
- **STRIDE F1-F3**: Information Disclosure - **МИТИГИРУЕТ**

### Implementation

- **Code**: `app/api/problem.py`, `app/api/error_handlers.py`
- **Tests**: `tests/test_security_errors.py`
- **PR**: [Link после создания]

### Standards

- **RFC 7807**: [RFC 7807](https://tools.ietf.org/html/rfc7807)
- **OWASP**: A01 - Broken Access Control

## Canary Rollout Strategy

### Фаза 3: Error Security Canary (Week 3-4)

#### Week 3: 10% Canary

- **Target**: 10% API requests получают RFC 7807 format
- **Config**: `ERROR_SECURITY_ENABLED=10` (percentage)
- **Success Criteria**:
  - 0% sensitive data leaks в error responses
  - Error correlation успешно traceable
  - No client integration issues

#### Week 4: Full Rollout

- **Config**: `ERROR_SECURITY_ENABLED=100`
- **Monitoring**: Error response compliance dashboard

### Emergency Rollback

- **Trigger**: Set `ERROR_SECURITY_ENABLED=0`
- **Effect**: Revert to legacy error format

## Implementation Status: DONE

### Pull Request

- **Commit**: [abc1234 - feat: implement RFC 7807 error response security](https://github.com/hse-secdev-2025-fall/course-project-DedovInside/commit/6f29ec73ba224d0ae06113615c0fd6d236c96044)

### Code Changes

- `app/api/problem.py` - реализация RFC 7807 с заголовками HTTP-статусов
- `app/api/error_handlers.py` - безопасная обработка ошибок, включая ошибки валидации
- `app/api/media.py` - удаление конфиденциальных данных из всех сообщений об ошибках
- `app/main.py` - обновление эндпоинтов для использования безопасных шаблонов ошибок
- `tests/test_error_security.py` - 8 комплексных тестов безопасности
- `tests/test_media.py` - обновление существующих тестов под формат RFC 7807
- `tests/test_errors.py` - обновление тестов ошибок валидации

### Test Coverage

## Тесты безопасности подтверждают соответствие требованиям

- 8 из 8 тестов безопасности пройдены
- Проверено: 0% утечки конфиденциальных данных в ответах
- Достигнуто 100% соответствие формату RFC 7807
- Все пути обработки ошибок покрыты безопасными сообщениями
- 17 из 17 существующих тестов обновлены и успешно проходят
- Все эндпоинты возвращают ошибки в едином формате RFC 7807
