# Data Flow Diagram (DFD)

## Media Catalog API - Архитектура и потоки данных

### Контекстная диаграмма

```mermaid
flowchart TB
    %% Внешние участники
    User["Пользователь<br/>Media Catalog"]
    Admin["Администратор<br/>Системы"]
    Scanner["Security Scanner<br/>CI/CD"]

    %% Границы доверия
    subgraph Internet["Internet - Untrusted Zone"]
        User
        Scanner
    end

    subgraph Edge["Edge Zone - DMZ"]
        LB["Load Balancer"]
        WAF["Web Application<br/>Firewall"]
    end

    subgraph Core["Core Zone - Trusted"]
        API["Media Catalog<br/>FastAPI Service"]
        subgraph App["Application Layer"]
            Auth["Auth Module<br/>(Future)"]
            Media["Media CRUD<br/>Operations"]
            Valid["Input Validation<br/>(Pydantic)"]
        end
    end

    subgraph Data["Data Zone - Restricted"]
        MemDB["In-Memory<br/>Media Database"]
        Logs["Application<br/>Logs"]
        Config["Configuration<br/>Secrets"]
    end

    %% Потоки данных (все подписи рёбер в кавычках для безопасности)
    User -->|"F1: HTTPS GET/POST<br/>Media Requests"| LB
    LB -->|"F2: HTTP Forward"| WAF
    WAF -->|"F3: Filtered Requests"| API

    API -->|"F4: Read/Write<br/>Media Data"| MemDB
    API -->|"F5: Log Events<br/>Audit Trail"| Logs
    API -->|"F6: Read Config<br/>Environment"| Config

    Admin -->|"F7: Monitor<br/>Health Checks"| API
    Admin -->|"F8: View Logs<br/>Security Events"| Logs

    Scanner -->|"F9: SAST/DAST<br/>Security Scans"| API
    Scanner -->|"F10: Dependency<br/>Vulnerability Check"| API

    %% Внутренние потоки
    API --> Auth
    API --> Media
    API --> Valid

    Auth -.->|"F11: User Context<br/>(Planned)"| Media
    Valid -->|"F12: Validated Data"| Media
    Media -->|"F13: Sanitized Queries<br/>user_id filtering"| MemDB

    %% Стили
    classDef untrusted fill:#000000,color:#ffffff,stroke:#f44336,stroke-width:2px
    classDef edge fill:#000000,color:#ffffff,stroke:#ff9800,stroke-width:2px
    classDef trusted fill:#000000,color:#ffffff,stroke:#4caf50,stroke-width:2px
    classDef data fill:#000000,color:#ffffff,stroke:#2196f3,stroke-width:2px


    class User,Scanner untrusted
    class LB,WAF edge
    class API,Auth,Media,Valid trusted
    class MemDB,Logs,Config data
```

### Детальная диаграмма - Media CRUD Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant V as Validator
    participant M as Media CRUD
    participant DB as Memory DB
    participant L as Logger

    Note over U,L: F1-F6: Типичный CRUD запрос

    U->>+API: F1: POST /media<br/>{"title": "Movie", "year": 2024}

    API->>+V: F2: Validate Input<br/>Pydantic Schema
    V-->>V: Check year (1800-2030)<br/>Check title (1-200 chars)
    V->>-API: F3: Validated Data

    API->>+M: F4: Create Media<br/>(data + user_id=1)
    M-->>M: Check Duplicate<br/>(title + year + user_id)
    M->>+DB: F5: Insert Media<br/>user_id filtering
    DB->>-M: F6: Created Media
    M->>-API: Media Response

    API->>+L: F7: Audit Log<br/>CREATE media_id=X user_id=1
    L->>-API: Logged

    API->>-U: 201 Created<br/>Media Response

    Note over U,L: NFR-03: Input Validation ✅<br/>NFR-06: Data Isolation ✅<br/>NFR-09: Audit Logging (Planned)
```

### Потоки данных (F1-F13)

| ID | Поток | Протокол | Данные | Угрозы (STRIDE) | Перевод |
|----|-------|----------|--------|-----------------|----------------------|
| **F1** | User → Load Balancer | HTTPS | HTTP Requests (JSON) | Man-in-the-middle, Request tampering | Перехват данных, подмена запросов |
| **F2** | LB → WAF | HTTP | Forwarded requests | Protocol downgrade | Понижение протокола безопасности |
| **F3** | WAF → FastAPI | HTTP | Filtered requests | Injection attacks | Инъекционные атаки |
| **F4** | API → Memory DB | In-process | Media objects | Data corruption | Повреждение данных |
| **F5** | API → Logs | File I/O | Log entries | Log injection | Инъекция в логи |
| **F6** | API → Config | Environment | Secrets, settings | Information disclosure | Раскрытие конфиденциальной информации |
| **F7** | Admin → API | HTTPS | Health checks | Privilege escalation | Повышение привилегий |
| **F8** | Admin → Logs | File access | Log viewing | Unauthorized access | Несанкционированный доступ |
| **F9** | Scanner → API | HTTPS | Security tests | False positives | Ложные срабатывания сканера |
| **F10** | Scanner → Dependencies | Package scan | Vulnerability data | Supply chain | Атаки на цепочку поставок |
| **F11** | Auth → Media | In-process | User context | Session hijacking | Захват сессии |
| **F12** | Validator → Media | In-process | Validated data | Validation bypass | Обход валидации |
| **F13** | Media → Memory DB | In-process | Filtered queries | Data isolation breach | Нарушение изоляции данных |

### Архитектурные решения безопасности

#### Текущие контроли

- **Input Validation** (NFR-03): Pydantic схемы на всех входах
- **Data Isolation** (NFR-06): user_id фильтрация в CRUD
- **Pre-commit Security** (NFR-04): Базовые хуки безопасности

#### Планируемые контроли

- **Rate Limiting** (NFR-08): Защита от DoS по F1
- **Request Size Limits** (NFR-07): Защита от больших payload по F3
- **Error Response Security** (NFR-13): Безопасные ошибки по F1-F3
- **Audit Logging** (NFR-09): Логирование по F4-F5
- **Content-Type Validation** (NFR-11): Строгая проверка по F1-F3

#### Будущие улучшения

- **Authentication & Authorization**: Замена заглушки CURRENT_USER_ID=1
- **HTTPS Enforcement**: TLS termination в Edge зоне
- **Database Security**: Переход с in-memory на реальную БД с шифрованием
