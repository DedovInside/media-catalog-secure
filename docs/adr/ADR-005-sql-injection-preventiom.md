# ADR-005: SQL Injection Prevention with SAST

**Дата:** 2025-10-18
**Статус:** Accepted
**Решение по:** Проактивная защита от SQL инъекций

## Context

### Проблема

Media Catalog API планирует переход с in-memory хранилища на реальную SQL базу данных:

```python
# Текущее состояние (безопасно):
def get_media_by_id(media_id: int, user_id: int) -> Optional[Media]:
    for media in _MEDIA_DB:  # In-memory list iteration
        if media.id == media_id and media.user_id == user_id:
            return media

# Будущее состояние с SQL (потенциально уязвимо):
def get_media_by_id(media_id: int, user_id: int) -> Optional[Media]:
    # ПОТЕНЦИАЛЬНАЯ SQL INJECTION:
    query = f"SELECT * FROM media WHERE id = {media_id} AND user_id = {user_id}"
    cursor.execute(query)

    # ЕЩЕ ХУЖЕ - user input:
    def search_media(title: str, user_id: int):
        query = f"SELECT * FROM media WHERE title LIKE '%{title}%' AND user_id = {user_id}"
        cursor.execute(query)  # title может содержать '; DROP TABLE media; --
```

### Security Risks из RISKS.md

- **R06**: SQL Injection в будущих версиях (L=2, I=4, Risk=8)
- **F4**: API → Database поток уязвим к Tampering

### Attack Scenarios

```python
# Scenario 1: Classic SQL Injection
POST /media {"title": "'; DROP TABLE media; --"}

# Scenario 2: Union-based data extraction
GET /media?title=' UNION SELECT user_id, password FROM users --

# Scenario 3: Blind SQL Injection
GET /media?title=' AND (SELECT COUNT(*) FROM users) > 0 --

# Scenario 4: Time-based injection
GET /media?title=' AND (SELECT sleep(10)) --
```

### P04 Risk Assessment

- **STRIDE: Tampering** через SQL injection в F4 потоке
- **Impact**: Data breach, unauthorized access, database corruption

## Decision

### Static Analysis Security Testing (SAST) with bandit

Принимаем **bandit SAST** как primary defense против SQL injection:

```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install bandit
        run: pip install bandit[toml]

      - name: Run SAST scan
        run: |
          bandit -r app/ -f json -o bandit-report.json
          # Fail build if High/Medium security issues found
          bandit -r app/ -ll  # Low-Low severity minimum
```

### Pre-commit Integration

```yaml
# .pre-commit-config.yaml - добавить к существующим хукам
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.5
  hooks:
    - id: bandit
      args: ['-r', 'app/', '-ll']  # Low severity minimum
      files: '^app/.*\.py$'
```

### Bandit Configuration

```toml
# pyproject.toml - bandit settings
[tool.bandit]
exclude_dirs = ["tests", "venv", ".venv"]
skips = ["B101"]  # Skip assert_used (OK in tests)

[tool.bandit.assert_used]
# Allow asserts in test files
skips = ["**/test_*.py", "**/tests/*.py"]
```

### Secure Database Layer (Future Implementation)

```python
# app/db/secure_queries.py - подготовка к SQL переходу
import asyncpg
from typing import Optional, List

class SecureMediaRepository:
    def __init__(self, connection_pool):
        self.pool = connection_pool

    async def get_media_by_id(self, media_id: int, user_id: int) -> Optional[dict]:
        """Secure parameterized query"""
        # БЕЗОПАСНО: Parameterized query
        query = """
            SELECT id, title, kind, year, description, status, rating, created_at
            FROM media
            WHERE id = $1 AND user_id = $2
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, media_id, user_id)
            return dict(row) if row else None

    async def search_media(self, title_pattern: str, user_id: int) -> List[dict]:
        """Secure search with parameterized LIKE"""
        # БЕЗОПАСНО: Pattern также параметризирован
        query = """
            SELECT id, title, kind, year, status
            FROM media
            WHERE title ILIKE $1 AND user_id = $2
            ORDER BY created_at DESC
            LIMIT 100
        """
        # Escape pattern для LIKE query
        safe_pattern = f"%{title_pattern.replace('%', '\\%').replace('_', '\\_')}%"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, safe_pattern, user_id)
            return [dict(row) for row in rows]

# bandit будет проверять что:
# НЕ ИСПОЛЬЗУЕТСЯ: string formatting в SQL
# НЕ ИСПОЛЬЗУЕТСЯ: f-strings с SQL
# ИСПОЛЬЗУЕТСЯ: parameterized queries ($1, $2, etc.)
```

## Alternatives

### Alternative 1: ORM Only (SQLAlchemy/Tortoise)

**Плюсы**: ORM защищает от SQL injection автоматически, type safety
**Минусы**: Performance overhead, не защищает от raw queries
**Вердикт**: **ДОПОЛНЯЕТ** SAST, планируется использовать SQLAlchemy + bandit

### Alternative 2: Dynamic Analysis (DAST)

**Плюсы**: Находит runtime SQL injection vulnerabilities
**Минусы**: Медленнее CI, требует running database, не catches all
**Вердикт**: Для staging/production testing, но SAST нужен для development

### Alternative 3: Manual Code Review

**Плюсы**: Human intelligence, business logic context
**Минусы**: Human error, не масштабируется, субъективность
**Вердикт**: Дополняет automation, но не основной метод

### Alternative 4: Runtime Protection (ModSecurity/WAF)

**Плюсы**: Blocks SQL injection на network level
**Минусы**: Не защищает internal queries, performance impact
**Вердикт**: Defense in depth, но не заменяет secure coding

### Alternative 5: Database Permissions

**Плюсы**: Minimal database privileges limit damage
**Минусы**: Не предотвращает injection, только снижает impact
**Вердикт**: Good practice, но не основная защита

## Consequences

### Положительные

- **Proactive Detection**: Находит SQL injection ДО production
- **CI Integration**: Автоматическая проверка каждого PR
- **Developer Education**: bandit объясняет why код небезопасен
- **Zero False Negatives**: Parameterized queries всегда безопасны
- **Performance**: SAST не влияет на runtime performance
- **Compliance**: SAST требуется многими security frameworks

### Отрицательные

- **False Positives**: bandit может срабатывать на безопасный код
- **CI Build Time**: Дополнительные 30-60 секунд на сборку
- **Tool Maintenance**: Обновление bandit rules и exceptions

### Компромиссы

- **Security vs Development Speed**: Additional CI step vs vulnerability prevention
- **Automation vs Flexibility**: Strict rules vs developer autonomy

## Security Impact

### Устраняемые угрозы

- **STRIDE F4: Tampering** через SQL injection в database layer
- **Data Breach** через unauthorized SELECT queries
- **Data Corruption** через malicious UPDATE/DELETE
- **Privilege Escalation** через database function injection

### OWASP Top 10 Coverage

- **A03: Injection** - SQL injection specifically targeted
- **A08: Software Integrity** - Secure coding practices enforcement

### Detection Capabilities

```python
# bandit обнаружит эти паттерны:
cursor.execute(f"SELECT * FROM media WHERE id = {media_id}")     # B608: hardcoded_sql_expressions
cursor.execute("SELECT * WHERE id = " + str(media_id))          # B608: sql_injection_vector
query = "SELECT * FROM media WHERE title = '%s'" % title        # B608: hardcoded_sql_expressions
db.query(f"UPDATE media SET title = '{new_title}'")             # B608: potential_sql_injection

# bandit НЕ СРАБОТАЕТ на безопасный код:
cursor.execute("SELECT * FROM media WHERE id = $1", (media_id,))  # Parameterized
query = "SELECT * FROM media WHERE user_id = ?"                   # Placeholder
conn.fetch("SELECT * FROM media WHERE id = $1 AND user_id = $2", media_id, user_id)
```

## Rollout Plan

### Фаза 1: SAST Setup (Week 1)

1. Add bandit to `requirements-dev.txt`
2. Configure bandit в `pyproject.toml`
3. Create security workflow `.github/workflows/security.yml`

### Фаза 2: Pre-commit Integration (Week 2)

1. Add bandit hook to `.pre-commit-config.yaml`
2. Test на existing codebase
3. Configure bandit exceptions если нужно

### Фаза 3: Database Preparation (Week 3)

1. Create secure repository pattern в `app/db/`
2. Write parameterized query examples
3. Add integration tests для database layer

### Фаза 4: Documentation & Training (Week 4)

1. Developer guidelines для secure SQL coding
2. Code review checklist with SQL injection focus
3. Security training materials

### Definition of Done

- [ ] bandit SAST running в CI/CD pipeline
- [ ] 0 High/Medium security findings в app/ directory
- [ ] Pre-commit hooks блокируют unsafe SQL patterns
- [ ] Secure database repository pattern implemented
- [ ] Developer documentation для SQL injection prevention
- [ ] Integration tests для parameterized queries

## Links

### P03 Security NFR

- **NFR-04**: SQL Injection Protection - **РЕАЛИЗУЕТ**

### P04 Threat Model

- **R06**: SQL Injection в будущих версиях (L=2, I=4, Risk=8) - **ЗАКРЫВАЕТ**
- **STRIDE F4**: Tampering через database queries - **МИТИГИРУЕТ**

### Implementation

- **CI**: `.github/workflows/security.yml`
- **Pre-commit**: `.pre-commit-config.yaml` bandit hook
- **Config**: `pyproject.toml` bandit settings
- **Dependencies**: `bandit[toml]==1.7.5`

### Standards & Tools

- **OWASP SQL Injection Prevention**: [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- **Bandit Documentation**: [Bandit Documentation](https://bandit.readthedocs.io/)
- **NIST SAST Guidelines**: SP 800-218 Secure Software Development Framework

## Canary Rollout Strategy

### Фаза 3: SAST Enforcement Canary (Week 3-4)

#### Week 3: Warning-Only Mode

- **Target**: Bandit runs но не блокирует CI
- **Config**: `BANDIT_FAIL_BUILD=false`
- **Success Criteria**:
  - 0 High/Critical findings в production code
  - CI build time increase < 30 seconds
  - No false positive blocking

#### Week 4: Blocking Mode

- **Config**: `BANDIT_FAIL_BUILD=true`
- **Effect**: CI fails если security issues found

### Emergency Rollback

- **Trigger**: Set `BANDIT_FAIL_BUILD=false`
- **Effect**: Continue builds but report security issues
