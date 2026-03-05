# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in LogSweeper, please report it responsibly by opening a private security advisory on this repository.

## Security Practices

- **No secrets in code**: All secrets are loaded from environment variables
- **Log redaction**: Sensitive fields (password, token, api_key, secret, authorization) are automatically redacted in API logs
- **CORS**: Configurable allowed origins (default: localhost only)
- **Input validation**: All API inputs are validated before processing
- **SQL injection prevention**: Parameterized queries throughout
- **RBAC scaffold**: Admin/user role configuration ready in config

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes      |
