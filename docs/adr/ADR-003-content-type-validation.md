# ADR-003: Content-Type Validation Security

**Дата:** 2025-10-18
**Статус:** Accepted
**Решение по:** Content-Type Confusion Prevention

## Context

### Проблема

FastAPI по умолчанию слишком толерантен к Content-Type headers:

```bash
# Принимается (нормально):
curl -X POST /media -H "Content-Type: application/json" -d '{"title": "Movie"}'

# ТОЖЕ принимается (потенциально опасно):
curl -X POST /media -H "Content-Type: text/plain" -d '{"title": "Movie"}'
curl -X POST /media -H "Content-Type: application/xml" -d '{"title": "Movie"}'
curl -X POST /media -d '{"title": "Movie"}'  # БЕЗ Content-Type!
```

### Security Risks

1. **Content-Type Confusion**: Обход валидации через неожиданные Content-Types
2. **Parser Confusion**: Разные парсеры могут интерпретировать данные по-разному
3. **XSS Preparation**: HTML/XML content может содержать scripts
4. **XXE Preparation**: XML External Entity атаки в будущем

### Attack Scenarios

```http
# Scenario 1: XSS через title field
POST /media HTTP/1.1
Content-Type: text/html
Content-Length: 52

{"title": "<script>alert('xss')</script>", "kind": "movie"}

# Scenario 2: XXE preparation
POST /media HTTP/1.1
Content-Type: application/xml
Content-Length: 150

<?xml version="1.0"?>
<!DOCTYPE media [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<media><title>&xxe;</title></media>
```

## Decision

### Strict Content-Type Enforcement

Принимаем **только `application/json`** для POST/PUT/PATCH requests:

```python
class StrictContentTypeMiddleware:
    def __init__(self, app, allowed_types: List[str] = None):
        self.app = app
        self.allowed_types = allowed_types or ["application/json"]

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] in ["POST", "PUT", "PATCH"]:
            headers = dict(scope.get("headers", []))
            content_type = headers.get(b"content-type", b"").decode().split(";")[0].strip()

            if content_type not in self.allowed_types:
                response = problem(
                    415,
                    "Unsupported Media Type",
                    f"Content-Type must be one of: {', '.join(self.allowed_types)}"
                )
                await send_response(response, send)
                return

        await self.app(scope, receive, send)
```

### Configuration

```python
# app/config.py
class APIConfig:
    ALLOWED_CONTENT_TYPES = ["application/json"]
    STRICT_CONTENT_TYPE = True  # Feature flag
```

### Error Response

```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.13",
  "title": "Unsupported Media Type",
  "status": 415,
  "detail": "Content-Type must be one of: application/json",
  "correlation_id": "abc123..."
}
```

## Alternatives

### Alternative 1: Whitelist + Accept additional types

**Плюсы**: Flexibility для будущего (XML API, form data)
**Минусы**: Increased attack surface, parser complexity
**Вердикт**: ❌ YAGNI для Media Catalog MVP

### Alternative 2: Content-Type + Magic Bytes validation

**Плюсы**: Defense in depth, catch Content-Type spoofing
**Минусы**: Overkill для JSON API, performance overhead
**Вердикт**: ❌ JSON не имеет reliable magic bytes

### Alternative 3: Framework-level validation (FastAPI dependency)

**Плюсы**: Cleaner code, route-specific rules
**Минусы**: Repeated code, easy to forget on new routes
**Вердикт**: ❌ Middleware обеспечивает consistent enforcement

### Alternative 4: Reverse proxy level (Nginx/Traefik)

**Плюсы**: Offload от application, early rejection
**Минусы**: Infrastructure dependency, configuration drift
**Вердикт**: ✅ Хорошее дополнение, но нужен application fallback

## Consequences

### Положительные

- **Attack Surface Reduction**: Только JSON parser используется
- **Parser Consistency**: Нет confusion между Content-Type и actual content
- **XSS Prevention**: HTML/XML content отклоняется на уровне middleware
- **XXE Prevention**: XML парсинг невозможен
- **API Clarity**: Явное указание supported media types

### Отрицательные

- **Client Strictness**: Клиенты должны правильно указывать Content-Type
- **Debugging Complexity**: 415 errors могут сбивать с толку
- **Future Limitation**: Усложнение добавления других форматов

### Компромиссы

- **Security vs Flexibility**: Строгость vs ability принимать разные форматы
- **Early Rejection vs Rich Validation**: 415 vs detailed validation errors

## Security Impact

### Устраняемые угрозы

- **STRIDE: Tampering** через Content-Type confusion в F1-F3
- **Content-Type Spoofing** attacks
- **Parser Confusion** vulnerabilities
- **Future XXE/XSS** через non-JSON content

### Defense Layers

```mermaid
Request → [Content-Type Check] → [JSON Parse] → [Pydantic Validation] → Business Logic
          415 if not JSON         400 if invalid   422 if schema error    Clean data
```

### Threat Landscape Evolution

- **Current**: Блокирует Content-Type confusion
- **Future**: Готовность к XML/HTML injection attempts
- **Compliance**: OWASP Input Validation guidelines

## Rollout Plan

### Фаза 1: Implementation (Week 1)\

1. Создать `StrictContentTypeMiddleware`
2. Добавить в `app/main.py` с feature flag
3. Unit tests для middleware behavior

### Фаза 2: Integration Testing (Week 2)

1. Integration tests для всех /media endpoints
2. Negative tests с различными Content-Type values
3. Contract tests для 415 error format

### Фаза 3: Gradual Rollout (Week 3)

1. Enable в development environment
2. Monitor для false positives
3. Production rollout с monitoring

### Фаза 4: Documentation (Week 4)

1. API documentation обновлена
2. Client SDK примеры с правильными headers
3. Troubleshooting guide для 415 errors

### Definition of Done

- [ ] Только `application/json` Content-Type принимается
- [ ] 415 errors в RFC 7807 format
- [ ] Negative tests покрывают various Content-Types
- [ ] API documentation содержит Content-Type requirements
- [ ] Zero false positives в production

## Links

### P03 Security NFR

- **NFR-11**: Content-Type Validation - **РЕАЛИЗУЕТ**
- **NFR-03**: Input Validation (дополняет) - **УКРЕПЛЯЕТ**

### P04 Threat Model

- **R11**: Content-Type confusion атаки (L=2, I=3, Risk=6) - **ЗАКРЫВАЕТ**
- **STRIDE F1-F3**: Tampering - **МИТИГИРУЕТ**

### Implementation

- **Code**: `app/middleware/content_type.py`
- **Tests**: `tests/test_content_type_validation.py`
- **Config**: `app/config.py`

### Standards

- **RFC 7231**: HTTP Content-Type semantics
- **RFC 7231**: HTTP 415 Unsupported Media Type
- **OWASP**: Input Validation Cheat Sheet

## Canary Rollout Strategy

### Фаза 3: Content-Type Validation Canary (Week 3-4)

#### Week 3: 20% Request Canary

- **Target**: 20% POST/PUT requests get strict validation
- **Config**: `CONTENT_TYPE_STRICT_PERCENTAGE=20`
- **Success Criteria**:
  - 0% false positive 415 rejections
  - All legitimate JSON requests pass
  - API client compatibility maintained

#### Week 4: Full Enforcement

- **Config**: `CONTENT_TYPE_STRICT_PERCENTAGE=100`
- **Result**: Only application/json accepted

### Emergency Rollback

- **Trigger**: Set `CONTENT_TYPE_STRICT_PERCENTAGE=0`
- **Effect**: Accept any Content-Type (legacy behavior)
