# HISTORY

## Project Context
- Repository in use: `rustams/b24pmo` (origin on VPS is `git@github.com:rustams/b24pmo.git`)
- Server: `85.239.54.74` (Ubuntu 24.04.3)
- Domain: `russalp.ru`
- Active stack: `frontend + php + postgres` (no CloudPub tunnel)
- Runtime mode: app is served via Docker Compose, proxied by Nginx, TLS via Let's Encrypt

## What Was Done (Chronological)

### 1) Initial VPS Provisioning
- Installed base tooling: `git`, `make`, `docker.io`, `docker compose plugin`, `nginx`, `certbot`, `python3-certbot-nginx`, `ufw`.
- Cloned project to `/opt/b24-ai-starter`.
- Created and configured `.env` manually (without `make dev-init`) to avoid CloudPub path.

### 2) Compose/Runtime Setup Without CloudPub
- Started stack with profiles:
  - `frontend`
  - `php`
  - `db-postgres`
- Added `docker-compose.override.yml` to bind frontend only on localhost:
  - `127.0.0.1:3000:3000`
- Kept backend/api internal for platform use and development.

### 3) Docker Hub Rate-Limit Mitigation
- Encountered Docker Hub anonymous pull limits (`429 Too Many Requests`).
- Switched base images to `mirror.gcr.io` in:
  - `frontend/Dockerfile`
  - `backends/php/docker/php-fpm/Dockerfile`
  - `backends/php/docker/php-cli/Dockerfile`
  - `docker-compose.yml` images for database/queue
- This was committed on VPS and pushed to current repo.

### 4) HTTPS + Nginx + Redirect
- Configured Nginx reverse proxy:
  - `https://russalp.ru/*` -> `http://127.0.0.1:3000`
- Issued Let's Encrypt certificate for `russalp.ru`.
- Enabled HTTP -> HTTPS redirect.
- Verified:
  - `http://russalp.ru` => `301`
  - `https://russalp.ru` => `200`

### 5) Service Persistence
- Added systemd unit for app startup:
  - `/etc/systemd/system/b24-ai-starter.service`
- Enabled service to start on boot.

### 6) Operational Commands
- Added helper scripts:
  - `/usr/local/bin/b24-deploy`
  - `/usr/local/bin/b24-status`
  - `/usr/local/bin/b24-logs`
- `b24-deploy master` does:
  - fetch + checkout + ff-only pull
  - restart `b24-ai-starter`
  - wait for `https://russalp.ru` health `200`

### 7) Git Remote Migration
- Switched remote from starter template repo to project repo:
  - `rustams/b24pmo`
- Pushed current branch (`master`) to new origin.

### 8) SSH Hardening + Deploy User
- Created `deploy` user for operations.
- Configured SSH key auth for `deploy`.
- Disabled insecure SSH options:
  - `PermitRootLogin no`
  - `PasswordAuthentication no`
  - `KbdInteractiveAuthentication no`
- Root SSH login is disabled.

### 9) Webhook Auto-Deploy
- Implemented webhook service:
  - `/usr/local/bin/b24-webhook.py`
  - `/etc/systemd/system/b24-webhook.service`
  - `/etc/b24/webhook.env` (contains secret and branch/repo restrictions)
- Added Nginx route:
  - `POST https://russalp.ru/deploy-webhook` -> webhook service (`127.0.0.1:9001`)
- Security checks in webhook:
  - Verifies `X-Hub-Signature-256` HMAC
  - Accepts only repo `rustams/b24pmo`
  - Accepts only ref `refs/heads/master`
  - Triggers `b24-deploy master` via `flock` lock

## Current Working Model

### Development flow
1. Work locally in Cursor on cloned `rustams/b24pmo`.
2. Commit and push to `master`.
3. GitHub webhook triggers deploy automatically on VPS.

### Manual operations on VPS (as `deploy`)
- `b24-status` - show git/services/containers/http health
- `b24-deploy master` - manual deploy
- `b24-logs 200` - tail logs

## Important Paths
- App: `/opt/b24-ai-starter`
- Nginx site: `/etc/nginx/sites-available/russalp.ru`
- App systemd unit: `/etc/systemd/system/b24-ai-starter.service`
- Webhook script: `/usr/local/bin/b24-webhook.py`
- Webhook unit: `/etc/systemd/system/b24-webhook.service`
- Webhook env/secret: `/etc/b24/webhook.env`
- Webhook log: `/var/log/b24-webhook.log`
- SSH hardening: `/etc/ssh/sshd_config.d/99-hardening.conf`

## Known Notes / Caveats
- Mirror registry (`mirror.gcr.io`) is intentionally used to avoid Docker Hub rate limits.
- Branch in use for deploy is `master`.
- Frontend is bound to localhost only; public ingress is only through Nginx.
- CloudPub is intentionally not used in this deployment.

## Verification Snapshot (at time of writing)
- `b24-ai-starter.service`: active
- `b24-webhook.service`: active
- `https://russalp.ru`: HTTP 200
- Webhook endpoint rejects unsigned requests and accepts signed `ping`/`push` payloads.

### 10) Repository Scope Cleanup to PHP + Frontend (March 8, 2026)
- Confirmed active development scope: `frontend + php` only.
- Removed unused backend stacks from repository tree:
  - `backends/node/*`
  - `backends/python/*`
- Removed non-relevant instructions to reduce context noise:
  - `instructions/node/*`
  - `instructions/python/*`
  - `instructions/queues/node.md`
  - `instructions/queues/python.md`
- Removed Node/Python development skills from both agent profiles:
  - `.cursor/skills/develop-b24-node`, `.cursor/skills/develop-b24-python`
  - `.claude/skills/develop-b24-node`, `.claude/skills/develop-b24-python`
- Updated remaining navigation/environment skills to explicitly reflect PHP + frontend only.
- Rewrote `instructions/knowledge.md` as a narrowed source-of-truth for the current stack.
- Removed non-essential duplicated/legacy context folders from working tree (`instructions/ai-hackathon-starter-full`, `versions/`) to keep local context focused.
- Prepared local on-demand Bitrix24 docs index:
  - cloned `https://github.com/bitrix24/b24restdocs` into local cache (`.cache/b24restdocs`)
  - generated file index for quick lookup (`.cache/b24restdocs.index.txt`)
  - usage model: consult only when needed for конкретный API/метод, not as default context preload.

### 11) Product Spec + Backend Migration to Python (March 8, 2026)
- Added product-level technical specification for PMO Hub:
  - `docs/PMO_HUB_PRODUCT_SPEC.md`
- Architecture decision updated:
  - primary backend switched to `Python (Django + b24pysdk)`
  - frontend remains `Nuxt 3`
- Repository structure refactored to Python-focused layout:
  - restored `backends/python/*`
  - removed `backends/php/*`
- Documentation and skills aligned to Python stack:
  - updated `instructions/knowledge.md`
  - restored/rewrote `instructions/python/*`
  - updated queue prompt and kept `instructions/queues/python.md`
  - switched skills to `develop-b24-python`, removed PHP skills
- Runtime config updated for Python-only operation:
  - rewritten `docker-compose.yml` to keep `api-python` and remove php/node services
  - rewritten `makefile` to keep `dev-python`/`prod-python` as main commands
  - removed `scripts/fix-php.sh` and refreshed `scripts/README.md`
  - adjusted `.env.example` (`SERVER_HOST=http://api-python:8000`)

### 12) Agent Context-Engineering Architecture Integration (March 8, 2026)
- Studied repository: `muratcankoylan/Agent-Skills-for-Context-Engineering` (skills + examples + docs).
- Imported full skill set into both agent environments:
  - `.cursor/skills/*`
  - `.claude/skills/*`
- Added top-level collection skill: `context-engineering-collection`.
- Added unified operating architecture documents:
  - `instructions/agents/knowledge.md`
  - `instructions/agents/skill-activation-map.md`
  - `instructions/agents/workflows.md`
- Added operational agent artifacts and templates:
  - `.agent/context/session-summary.md`
  - `.agent/context/decision-log.jsonl`
  - `.agent/context/artifact-index.jsonl`
  - `.agent/plans/current-plan.md`
  - `.agent/evaluation/rubric.md`
- Linked architecture into project entry points:
  - updated `instructions/knowledge.md`
  - updated `README.md` with unified agent architecture section.

### 13) Backend Modularization for PMO Feature Blocks (March 8, 2026)
- Refactored Python backend from monolithic endpoint layout to feature-oriented structure.
- Added `backends/python/api/main/features/` with dedicated modules:
  - `common`, `installer`, `strategy`, `delivery`, `resources`, `risks`, `budget`, `meetings`, `sync`, `rbac`
- Moved endpoint logic into module-local `views.py` and business placeholders into `services.py`.
- Kept compatibility for existing endpoints (`/api`, `/api/health`, `/api/install`, `/api/getToken`) via facade and route preservation.
- Added PMO scaffold routes under `/api/pmo/*` to match product specification domains and support incremental implementation.
- Added architecture doc: `docs/BACKEND_CODE_STRUCTURE.md`.
- Updated agent memory artifacts (`.agent/context/*`, `.agent/plans/*`) with decisions and artifact index for this restructuring task.
