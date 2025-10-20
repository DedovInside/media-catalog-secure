# ADR-002: Request Protection (Size & Rate Limiting)

**Дата:** 2025-10-18
**Статус:** Accepted
**Решение по:** DoS Protection для Media Catalog API

## Context

### Проблема

Media Catalog API в текущем состоянии уязвим к DoS атакам:

```python
# Текущие уязвимости:
# 1. FastAPI принимает запросы любого размера
# 2. Нет ограничений на частоту запросов
# 3. Нет защиты от медленных клиентов

# Потенциальные атаки:
POST /media
Content-Length: 1073741824  # 1GB JSON payload

# Или:
for i in range(10000):
    requests.post("/media", json=large_payload)  # Flood attack
```

### Business Impact

- **Service Unavailability**: Перегрузка сервера большими запросами
- **Resource Exhaustion**: Исчерпание памяти и CPU
- **Legitimate User Impact**: Замедление для реальных пользователей
- **Infrastructure Costs**: Избыточное потребление ресурсов

### P04 Risk Assessment

- **R03**: DoS через большие запросы (L=3, I=4, Risk=12)
- **R04**: DoS через высокую частоту (L=4, I=3, Risk=12)

## Decision

### Request Size Limiting

Ограничиваем размер HTTP requests до **1MB** через ASGI middleware:

```python
class RequestSizeLimitMiddleware:
    def __init__(self, app, max_size: int = 1024 * 1024):  # 1MB default
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] in ["POST", "PUT", "PATCH"]:
            content_length = scope.get("headers", {}).get(b"content-length")
            if content_length and int(content_length) > self.max_size:
                # Return 413 Payload Too Large per RFC 7231
                response = problem(413, "Payload Too Large",
                                 f"Request size exceeds {self.max_size} bytes")
                await send_response(response, send)
                return
        await self.app(scope, receive, send)
```

### Rate Limiting

Ограничиваем частоту до **100 requests/minute per IP** через slowapi:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("")
@limiter.limit("100/minute")  # NFR-08 requirement
async def create_media(request: Request, media_data: MediaCreate):
    # ... implementation
```

### Configuration

```python
# app/config.py
class SecurityConfig:
    MAX_REQUEST_SIZE = 1024 * 1024  # 1MB (NFR-07)
    RATE_LIMIT_REQUESTS = 100       # per minute (NFR-08)
    RATE_LIMIT_WINDOW = 60          # seconds
    RATE_LIMIT_KEY = "ip"           # or "user" when auth added
```

## Alternatives

### Alternative 1: Nginx/Proxy-level protection

**Плюсы**: Offload от application, reverse proxy optimization
**Минусы**: Infrastructure dependency, configuration complexity
**Вердикт**: Хорошее дополнение, но не замена application-level controls

### Alternative 2: Cloud-based WAF (Cloudflare, AWS WAF)

**Плюсы**: Professional DoS protection, global edge network
**Минусы**: Vendor lock-in, additional costs, external dependency
**Вердикт**: Для production, но нужен fallback на application level

### Alternative 3: Token bucket vs Fixed window

**Плюсы Token Bucket**: Burst allowance, smoother rate limiting
**Плюсы Fixed Window**: Simplicity, predictable behavior
**Решение**: Fixed window для MVP, token bucket для v2.0

### Alternative 4: Per-user vs Per-IP limiting

**Per-IP**: Проще реализовать, защищает от внешних атак
**Per-User**: Более точный контроль, но требует аутентификации
**Решение**: Per-IP сейчас, per-user когда добавим auth

## Consequences

### Положительные

- **DoS Resilience**: Защита от memory exhaustion и flooding
- **Resource Protection**: Predictable memory/CPU usage
- **Fair Usage**: Равномерное распределение ресурсов между пользователями
- **Cost Control**: Предотвращение избыточного потребления
- **SLA Protection**: Stable performance для legitimate users

### Отрицательные

- **False Positives**: Legitimate users за NAT могут пострадать
- **Complexity**: Дополнительная логика и configuration
- **Monitoring Overhead**: Нужны metrics для rate limiting

### Компромиссы

- **Security vs Usability**: Строгие лимиты vs user convenience
- **Performance vs Protection**: Overhead от middleware vs security benefits

## Security Impact

### Устраняемые угрозы

- **STRIDE: Denial of Service** в потоках F1-F3
- **Resource Exhaustion** attacks
- **Slow HTTP** attacks (медленные клиенты)
- **Application-layer flooding**

### Defense in Depth

```mermaid
Internet → [Cloud WAF] → [Reverse Proxy] → [App Middleware] → FastAPI
           Rate Limit     Size Limit      Rate+Size Limit    Validation
```

### Мониторинг и алертинг

- **Metrics**: Request size distribution, rate limit violations
- **Alerts**: High rate of 413/429 responses, unusual traffic patterns
- **Dashboards**: Real-time traffic monitoring

## Rollout Plan

### Фаза 1: Size Limiting (Week 1)

1. Создать `RequestSizeLimitMiddleware` в `app/middleware/`
2. Добавить в `app/main.py` с configuration
3. Tests для 413 responses при больших requests

### Фаза 2: Rate Limiting (Week 2)

1. Интегрировать `slowapi` dependency
2. Применить `@limiter.limit()` к эндпоинтам /media
3. Tests для 429 responses при превышении лимитов

### Фаза 3: Monitoring (Week 3)

1. Добавить metrics collection для middleware
2. Dashboard для мониторинга request patterns
3. Alert rules для DoS detection

### Фаза 4: Tuning (Week 4)

1. Load testing для определения оптимальных лимитов
2. A/B testing с разными rate limits
3. Documentation для операционной команды

### Definition of Done

- [ ] Requests > 1MB возвращают 413 Payload Too Large
- [ ] Requests > 100/min возвращают 429 Too Many Requests
- [ ] RFC 7807 format для всех error responses
- [ ] Negative tests покрывают DoS scenarios
- [ ] Monitoring и alerting настроены

## Links

### P03 Security NFR

- **NFR-07**: Request Size Limits ≤ 1MB - **РЕАЛИЗУЕТ**
- **NFR-08**: Rate Limiting ≤ 100 req/min - **РЕАЛИЗУЕТ**

### P04 Threat Model

- **R03**: DoS через большие запросы (Risk=12) - **ЗАКРЫВАЕТ**
- **R04**: DoS через высокую частоту (Risk=12) - **ЗАКРЫВАЕТ**
- **STRIDE F1-F3**: Denial of Service - **МИТИГИРУЕТ**

### Implementation

- **Code**: `app/middleware/request_protection.py`
- **Config**: `app/config.py`
- **Tests**: `tests/test_request_protection.py`
- **Dependencies**: `slowapi==0.1.9`

### Standards

- **RFC 7231**: HTTP 413 Payload Too Large
- **RFC 6585**: HTTP 429 Too Many Requests
- **OWASP**: DoS Prevention Cheat Sheet

## Canary Rollout Strategy

### Фаза 3: DoS Protection Canary (Week 3-4)

#### Week 3: 10% IP Canary

- **Target**: 10% IP addresses получают rate limiting
- **Config**: `RATE_LIMIT_PERCENTAGE=10`
- **Success Criteria**:
  - 429 error rate < 5% от всех requests
  - p95 latency increase < 10% baseline
  - No legitimate user complaints

#### Week 4: Size Limits Expansion

- **Config**: `SIZE_LIMIT_PERCENTAGE=50` + `RATE_LIMIT_PERCENTAGE=50`
- **Monitoring**: Request size distribution + 413 errors

### Emergency Rollback

- **Trigger**: Set both percentages to 0
- **RTO**: < 2 minutes via environment variables
