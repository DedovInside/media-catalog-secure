# Media Catalog Secure

[![CI/CD Pipeline](https://github.com/DedovInside/media-catalog-secure/actions/workflows/ci.yml/badge.svg)](https://github.com/DedovInside/media-catalog-secure/actions/workflows/ci.yml)
[![Docker Image](https://ghcr-badge.deta.dev/dedovinside/media-catalog-secure/latest_tag?trim=major&label=Docker)](https://github.com/DedovInside/media-catalog-secure/pkgs/container/media-catalog-secure)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112.2-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://postgresql.org)

**Secure media catalog API** for tracking movies, courses, and other content with advanced security features.

## ✨ Features

- 🎬 **Media Management**: Track movies, courses, books with ratings and watch status
- 🔐 **HashiCorp Vault Integration**: Secure secrets management
- 🛡️ **Security Hardening**: Input validation, SQL injection prevention, security headers
- 🚀 **Async API**: FastAPI with async/await PostgreSQL operations
- 🐳 **Containerized**: Multi-stage Docker builds with non-root user
- 🧪 **Comprehensive Testing**: Unit tests, integration tests, security scans
- 📊 **CI/CD Pipeline**: GitHub Actions with matrix builds, caching, and deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ 
- PostgreSQL 15+
- HashiCorp Vault (for secrets management)
- Docker & Docker Compose (optional)