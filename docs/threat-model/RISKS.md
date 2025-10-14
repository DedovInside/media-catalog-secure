# Risk Register

## Media Catalog API - Реестр рисков и план обработки

### Методология оценки рисков

#### Шкала вероятности (L - Likelihood)

- 1 - Очень низкая (< 5%)
- 2 - Низкая (5-25%)
- 3 - Средняя (25-50%)
- 4 - Высокая (50-75%)
- 5 - Очень высокая (> 75%)

#### Шкала воздействия (I - Impact)

- 1 - Незначительное (косметические проблемы)
- 2 - Низкое (локальные проблемы)
- 3 - Среднее (функциональные проблемы)
- 4 - Высокое (частичная недоступность)
- 5 - Критическое (полная недоступность, утечка данных)

#### Матрица рисков (Risk = L × I)

- 1-4: Низкий риск (зеленый)
- 5-9: Средний риск (желтый)
- 10-15: Высокий риск (оранжевый)
- 16-25: Критический риск (красный)

### Реестр рисков

| Risk ID | Описание риска | Связанные потоки/NFR | L | I | Risk | Категория | Стратегия | Владелец | Срок | Критерий закрытия |
|---------|----------------|---------------------|---|---|------|-----------|-----------|----------|------|-------------------|
| **R01** | 🔴 **Межпользовательский доступ к данным** | F4, F13 / NFR-06 | 2 | 5 | **10** | Data Security | ✅ **Снижен** | @DedovInside | ✅ 2025.10.06 | ✅ 100% CRUD операций с user_id фильтрацией |
| **R02** | 🔴 **XSS через недостаточную валидацию** | F1-F3 / NFR-03 | 2 | 5 | **10** | Input Security | ✅ **Снижен** | @DedovInside | ✅ 2025.10.06 | ✅ Pydantic валидация + 17 автоматических тестов |
| **R03** | 🟠 **DoS через большие запросы** | F1-F3 / NFR-07 | 3 | 4 | **12** | Availability | **Снизить** | @DedovInside | 2025.11.15 | FastAPI request size limit ≤ 1MB + тесты 413 |
| **R04** | 🟠 **DoS через высокую частоту запросов** | F1-F3 / NFR-08 | 4 | 3 | **12** | Availability | **Снизить** | @DedovInside | 2025.11.15 | Rate limiting ≤ 100 req/min + тесты 429 |
| **R05** | 🟠 **Information disclosure через ошибки** | F1-F3 / NFR-13 | 3 | 4 | **12** | Information Security | **Снизить** | @DedovInside | 2025.10.25 | 0% sensitive data в error responses + security тесты |
| **R06** | 🟡 **SQL Injection в будущих версиях** | F4 / NFR-04 | 2 | 4 | **8** | Code Security | **Снизить** | @DedovInside | 2025.10.30 | bandit SAST в CI + 0 security findings |
| **R07** | 🟡 **Уязвимые зависимости** | F10 / NFR-05 | 3 | 3 | **9** | Supply Chain | **Снизить** | @DedovInside | 2025.10.30 | safety scanning в CI + High/Critical ≤ 3 дня SLA |
| **R08** | 🟡 **Раскрытие секретов в коде** | F6 / NFR-10 | 2 | 3 | **6** | Configuration Security | **Снизить** | @DedovInside | 2025.11.01 | detect-secrets в pre-commit + 0 найденных секретов |
| **R09** | 🟡 **Отсутствие аудита действий** | F5 / NFR-09 | 3 | 3 | **9** | Compliance | **Снизить** | @DedovInside | 2025.11.30 | 100% CRUD операций логируются + structured logs |
| **R10** | 🟡 **Log injection атаки** | F5 / NFR-09 | 2 | 3 | **6** | Integrity | **Снизить** | @DedovInside | 2025.11.30 | Log sanitization + structured logging |
| **R11** | 🟡 **Content-Type confusion атаки** | F1-F3 / NFR-11 | 2 | 3 | **6** | Input Security | **Снизить** | @DedovInside | 2025.11.30 | Только application/json + тесты 415 |
| **R12** | 🟢 **Производительная деградация** | F1-F3 / NFR-01, NFR-02 | 2 | 2 | **4** | Performance | **Снизить** | @DedovInside | 2025.12.15 | p95 ≤ 200ms + error rate ≤ 1% мониторинг |

### Текущий статус рисков

#### Закрытые риски (2)

- **R01**: Data isolation breach - **РЕШЕН** через user_id фильтрацию
- **R02**: XSS vulnerability - **РЕШЕН** через Pydantic валидацию

#### Активные (в работе) - 3

- **R05**: Information disclosure - Issue #15, в работе
- **R06**: SQL Injection protection - Issue #10, добавляем bandit
- **R07**: Vulnerable dependencies - Issue #10, добавляем safety

#### Запланированные (7)

- **R03, R04**: DoS protection - Issue #12, milestone 2025.11
- **R08**: Secret management - Issue #10, milestone 2025.10
- **R09, R10**: Audit logging - Issue #13, milestone 2025.11
- **R11**: Content-Type validation - Issue #14, milestone 2025.11
- **R12**: Performance monitoring - Issues #7, #8, milestone 2025.12

### Детальный план обработки рисков

#### 🔴 Критические/Высокие риски (R03-R05)

#### R03: DoS через большие запросы

```python
# Текущее состояние: FastAPI принимает запросы любого размера
# Цель: Ограничить до 1MB

# Планируемая реализация:
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 1024 * 1024):  # 1MB
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_size:
                raise HTTPException(413, "Payload too large")
        return await call_next(request)

# Тесты:
def test_large_request_rejected():
    large_payload = "x" * (2 * 1024 * 1024)  # 2MB
    response = client.post("/media", json={"title": large_payload})
    assert response.status_code == 413
```

#### R04: DoS через высокую частоту

```python
# Планируемая реализация с slowapi:
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("")
@limiter.limit("100/minute")  # NFR-08: ≤ 100 req/min на IP
def create_media(request: Request, media_data: MediaCreate):
    # ... existing logic
```

#### R05: Information disclosure

```python
# Текущая проблема в app/api/media.py:
raise ApiError(
    code="not_found",
    message=f"Media with id {media_id} not found",  # Раскрывает ID
    status=404
)

# Планируемое исправление:
raise ApiError(
    code="not_found",
    message="Resource not found",  # ✅ Безопасно
    status=404
)
```

#### 🟡 Средние риски (R06-R11)

#### R06: SQL Injection protection

```yaml
# Добавление в .pre-commit-config.yaml:
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.5
  hooks:
    - id: bandit
      args: ['-r', '.', '-f', 'json', '-o', 'bandit-report.json']
```

#### R07: Уязвимые зависимости

```yaml
# Добавление в .github/workflows/ci.yml:
- name: Security scan dependencies
  run: |
    pip install safety
    safety check --json --output safety-report.json
    # Fail build if High/Critical vulnerabilities found
```

### Принятые риски

| Risk ID | Обоснование принятия | Митигация | Мониторинг |
|---------|---------------------|-----------|------------|
| **R12** | Производительность не критична для MVP Media Catalog | Базовый мониторинг времени отклика | Quarterly review производительности |

### Отложенные риски (будущие версии)

| Risk ID | Описание | Причина отложения | Планируемая версия |
|---------|----------|-------------------|-------------------|
| **R-F1** | Weak password hashing | Нет аутентификации в текущей версии | v2.0 (с добавлением auth) |
| **R-F2** | Session hijacking | Нет сессий в текущей версии | v2.0 (с добавлением auth) |
| **R-F3** | HTTPS enforcement | Deployment scope, не приложение | v1.5 (production deployment) |

### Связь с GitHub Issues и Milestones

#### Milestone 2025.10 (Critical Security) - 4 риска

- **R01, R02**: Уже решены (data isolation + input validation)
- **R05**: Information disclosure - Issue #15
- **R06, R07**: SAST + Dependencies - Issue #10

#### Milestone 2025.11 (DoS Protection) - 4 риска

- **R03, R04**: DoS protection - Issue #12
- **R09, R10**: Audit logging - Issue #13
- **R11**: Content-Type validation - Issue #14

#### Milestone 2025.12 (Performance) - 1 риск

- **R12**: Performance monitoring - Issues #7, #8
