# ADR-004: Secret Management with HashiCorp Vault

**Дата:** 2025-10-18
**Статус:** Accepted
**Решение по:** Безопасное управление секретами и конфигурацией

## Context

### Проблема

Media Catalog API будет содержать чувствительную конфигурацию при переходе к production:

```python
# Текущие и будущие секреты:
# 1. Database credentials (при переходе с in-memory на PostgreSQL)
DATABASE_URL = "postgresql://user:password@host:5432/db"  # Хардкод в коде

# 2. JWT secrets (при добавлении аутентификации)
JWT_SECRET_KEY = "super-secret-key-12345"  # В переменных окружения

# 3. External API keys (для интеграций)
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9..."  # В .env файлах

# 4. Monitoring secrets
SENTRY_DSN = "https://abc123@sentry.io/project"  # В логах
```

### Security Risks из RISKS.md

- **R08**: Раскрытие секретов в коде (L=2, I=3, Risk=6)
- **F6**: Information disclosure через Config (NFR-10)

### Business Impact

- **Data Breach**: Скомпрометированные DB credentials → полная утечка данных
- **Service Compromise**: Украденные API ключи → несанкционированное использование
- **Compliance Violations**: Секреты в Git → нарушение security policies
- **Operational Risk**: Manual secret management → human errors

## Decision

### HashiCorp Vault Integration

Принимаем **Vault как centralized secret store** с local mock для development:

```python
# app/secrets/vault_client.py
import hvac
import os
from typing import Dict, Optional
from functools import lru_cache

class VaultClient:
    def __init__(self):
        self.vault_url = os.environ.get("VAULT_URL", "http://localhost:8200")
        self.vault_token = os.environ.get("VAULT_TOKEN", "dev-token")
        self.client = hvac.Client(url=self.vault_url, token=self.vault_token)

    @lru_cache(maxsize=128)  # Cache secrets for performance
    def get_secret(self, path: str) -> Dict[str, str]:
        """Get secret from Vault KV store"""
        try:
            if self.client.is_authenticated():
                response = self.client.secrets.kv.v2.read_secret_version(path=path)
                return response['data']['data']
            else:
                return self._get_dev_secrets(path)
        except Exception as e:
            print(f"Vault error: {e}, falling back to dev secrets")
            return self._get_dev_secrets(path)

    def _get_dev_secrets(self, path: str) -> Dict[str, str]:
        """Development fallback secrets"""
        dev_secrets = {
            "media-catalog/database": {
                "url": "postgresql://dev_user:dev_pass@localhost:5432/media_dev",
                "password": "dev-database-password",
                "ssl_mode": "prefer"
            },
            "media-catalog/api": {
                "jwt_secret": "dev-jwt-secret-key-not-for-production",
                "session_secret": "dev-session-secret-key"
            },
            "media-catalog/external": {
                "tmdb_api_key": "dev-tmdb-api-key",
                "sentry_dsn": "dev-sentry-dsn"
            }
        }
        return dev_secrets.get(path, {})

# app/config.py - Configuration with Vault
vault_client = VaultClient()

class Config:
    """Configuration management with Vault integration"""

    @property
    def database_url(self) -> str:
        secrets = vault_client.get_secret("media-catalog/database")
        return secrets.get("url", "sqlite:///./fallback.db")

    @property
    def jwt_secret_key(self) -> str:
        secrets = vault_client.get_secret("media-catalog/api")
        return secrets["jwt_secret"]

    @property
    def tmdb_api_key(self) -> Optional[str]:
        secrets = vault_client.get_secret("media-catalog/external")
        return secrets.get("tmdb_api_key")
```

### Vault Policies & Access Control

```hcl
# vault/policies/media-catalog-dev.hcl
path "secret/data/media-catalog/*" {
  capabilities = ["read"]
}

# vault/policies/media-catalog-prod.hcl
path "secret/data/media-catalog/database" {
  capabilities = ["read"]
}
path "secret/data/media-catalog/api" {
  capabilities = ["read"]
}
```

### Secret Rotation Strategy

```python
# app/secrets/rotation.py
class SecretRotationService:
    def __init__(self, vault_client: VaultClient):
        self.vault = vault_client

    async def rotate_jwt_secret(self):
        """Rotate JWT secret weekly"""
        import secrets
        new_secret = secrets.token_urlsafe(32)

        # Update in Vault
        self.vault.client.secrets.kv.v2.create_or_update_secret(
            path="media-catalog/api",
            secret={"jwt_secret": new_secret}
        )

        # Notify application instances to refresh
        await self._notify_app_refresh()
```

## Alternatives

### Alternative 1: Environment Variables

**Плюсы**: Simple, 12-factor app compliance, no external dependencies
**Минусы**: No rotation, visible in process list, manual management at scale
**Вердикт**: Не подходит для production, нет centralized management

### Alternative 2: AWS Secrets Manager

**Плюсы**: Managed service, automatic rotation, AWS integration
**Минусы**: Vendor lock-in, AWS dependency, additional costs
**Вердикт**: Хорошо для AWS environments, но Vault более universal

### Alternative 3: Azure Key Vault

**Плюсы**: Enterprise features, Microsoft ecosystem integration
**Минусы**: Vendor lock-in, Azure dependency, complex for simple cases
**Вердикт**: Подходит для Azure deployments

### Alternative 4: Kubernetes Secrets

**Плюсы**: Platform-native, encrypted at rest
**Минусы**: K8s dependency, no rotation, base64 encoding only
**Вердикт**: Не enterprise-grade secret management

### Alternative 5: Docker Swarm Secrets

**Плюсы**: Built-in to Docker Swarm, simple to use
**Минусы**: Limited features, no rotation, Docker dependency
**Вердикт**: Устаревшая технология, ограниченный функционал

## Consequences

### Положительные

- **Centralized Management**: Единое место управления всеми секретами
- **Access Control**: Fine-grained policies для разных environments
- **Audit Trail**: Все обращения к секретам логируются
- **Secret Rotation**: Automated rotation для enhanced security
- **High Availability**: Vault clustering для production resilience
- **Encryption**: Секреты encrypted at rest и in transit
- **Multi-Environment**: Dev/staging/prod isolation

### Отрицательные

- **Infrastructure Complexity**: Дополнительный сервис для управления
- **Single Point of Failure**: Vault недоступен → app не может стартовать
- **Learning Curve**: Команда должна изучить Vault concepts
- **Operational Overhead**: Monitoring, backup, upgrade Vault

### Компромиссы

- **Security vs Complexity**: Enterprise security vs simple env vars
- **Flexibility vs Dependency**: Powerful secret management vs external service
- **Performance vs Security**: Secret caching vs fresh data

## Security Impact

### Устраняемые угрозы

- **STRIDE F6: Information Disclosure** через config files
- **Source Code Analysis** attacks через Git history
- **Environment Variable Exposure** в production
- **Manual Secret Sharing** через insecure channels

### Defense in Depth

```mermaid
Application → [Config Layer] → [Vault Client] → [Vault Server] → [Encrypted Storage]
              Cache secrets    Auth + Request   Policies      AES-256 + TLS
```

### Compliance Benefits

- **SOX/PCI**: Centralized secret management с audit trail
- **GDPR**: Секреты не в logs или source code
- **SOC2**: Access controls и encryption requirements

### Threat Model Coverage (из STRIDE.md)

- **F6: API → Config** - Vault защищает от secret disclosure
- **R08**: Раскрытие секретов в коде - полностью устраняется

## Rollout Plan

### Фаза 1: Local Development (Week 1)

1. Setup Vault dev server: `vault server -dev`
2. Implement `VaultClient` с fallback на dev secrets
3. Create basic policies для media-catalog paths

### Фаза 2: Application Integration (Week 2)

1. Integrate Vault client в `app/config.py`
2. Replace hardcoded secrets с Vault calls
3. Add secret caching для performance

### Фаза 3: Production Setup (Week 3)

1. Deploy Vault cluster в production
2. Configure authentication (AppRole/K8s auth)
3. Migrate secrets from environment variables

### Фаза 4: Automation & Monitoring (Week 4)

1. Secret rotation workflows
2. Vault monitoring и alerting
3. Backup и disaster recovery procedures

### Definition of Done

- [ ] Vault server deployed в dev/staging/prod
- [ ] 0% hardcoded secrets в application code
- [ ] All secrets managed через Vault KV store
- [ ] Access policies configured для different roles
- [ ] Secret rotation implemented для JWT keys
- [ ] Monitoring и alerting для Vault health

## Links

### P03 Security NFR

- **NFR-10**: Secret Management - **РЕАЛИЗУЕТ**

### P04 Threat Model

- **R08**: Раскрытие секретов в коде (L=2, I=3, Risk=6) - **ЗАКРЫВАЕТ**
- **STRIDE F6**: Information Disclosure через Config - **МИТИГИРУЕТ**

### Implementation

- **Code**: `app/secrets/vault_client.py`, `app/config.py`
- **Infrastructure**: `vault/` configuration files
- **Tests**: `tests/test_secret_management.py`
- **Dependencies**: `hvac==1.2.1` (HashiCorp Vault client)

### Standards & Documentation

- **HashiCorp Vault**: [HashiCorp Vault](https://vaultproject.io/docs)
- **OWASP Secret Management**: Cryptographic Storage Cheat Sheet
- **NIST SP 800-57**: Key Management Guidelines
- **12-Factor App**: Config section compliance

## Canary Rollout Strategy

### Фаза 3: Vault Migration Canary (Week 3-4)

#### Week 3: Non-Critical Secrets

- **Target**: External API keys migration to Vault first
- **Config**: `VAULT_ENABLED_SECRETS=["external"]`
- **Success Criteria**:
  - Vault connectivity 99.9% uptime
  - Secret retrieval latency < 50ms p95
  - No service interruptions

#### Week 4: Critical Secrets Migration

- **Target**: Database credentials to Vault
- **Config**: `VAULT_ENABLED_SECRETS=["external", "database", "api"]`
- **Monitoring**: Application startup success rate

### Emergency Rollback

- **Trigger**: Set `VAULT_ENABLED_SECRETS=[]`
- **Effect**: Fallback to environment variables
- **RTO**: < 1 minute (cached secrets)
