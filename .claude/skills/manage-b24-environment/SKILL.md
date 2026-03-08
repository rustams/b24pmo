---
name: manage-b24-environment
description: Manage the Python + frontend Bitrix24 development environment with Docker, Makefile, and Cloudpub.
---

# Manage Bitrix24 Environment (Python + Frontend)

## Common Commands

```bash
# Start
make dev-init
make dev-python

# Stop and logs
make down
make logs

# Security
make security-scan
make security-tests
```

## Queue (optional)

```bash
make queue-up
make queue-down
```

Use RabbitMQ only when `ENABLE_RABBITMQ=1` is set in `.env`.

## Environment Notes

- Main config: `.env`
- Frontend public URL: `VIRTUAL_HOST`
- Backend target from frontend: `SERVER_HOST=http://api-python:8000`
- OAuth credentials: `CLIENT_ID`, `CLIENT_SECRET`

## Troubleshooting

- Cloudpub issues: verify `CLOUDPUB_TOKEN`
- JWT issues: verify `JWT_SECRET`
- Backend connectivity: verify `SERVER_HOST` and running `api-python`
