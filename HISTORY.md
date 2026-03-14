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

### 14) Frontend Modularization Aligned with PMO Backend Domains (March 8, 2026)
- Refactored frontend into feature-oriented PMO architecture.
- Added `frontend/app/features/pmo/` with domain modules:
  - `strategy`, `delivery`, `resources`, `risks`, `budget`, `meetings`, `sync`, `rbac`
- Added module-level API adapters (`api.ts`) mapped to backend endpoints under `/api/pmo/*`.
- Added reusable PMO components:
  - `PmoModuleCard.vue`
  - `PmoOverviewPanel.vue`
- Added PMO domain store:
  - `frontend/app/stores/pmo.ts`
- Extended shared API transport in `frontend/app/stores/api.ts`:
  - `authGet`, `authPost` for consistent authenticated backend calls.
- Added new PMO pages:
  - `/pmo`, `/pmo/strategy`, `/pmo/delivery`, `/pmo/resources`, `/pmo/risks`, `/pmo/budget`, `/pmo/meetings`, `/pmo/sync`, `/pmo/rbac`
- Linked main page to PMO Hub (`Open PMO Hub` action on `index.client.vue`).
- Added architecture doc: `docs/FRONTEND_CODE_STRUCTURE.md`.
- Updated `.agent` memory artifacts (plan, summary, decision log, artifact index) for this task.

### 15) Delivery Roadmap + Bitrix24 Task Automation (March 8, 2026)
- Added implementation roadmap document aligned with PMO Hub product specification:
  - `docs/DELIVERY_ROADMAP.md`
- Added machine-readable roadmap task graph for deterministic planning and task creation:
  - `docs/ROADMAP_TASKS.json`
- Added status sync template for roadmap execution tracking:
  - `docs/ROADMAP_STATUS.example.json`
- Implemented Bitrix24 webhook automation CLI:
  - `scripts/bitrix24/roadmap_sync.py`
  - supports dry-run and apply modes
  - creates project tasks via `tasks.task.add`
  - links dependencies via `task.dependence.add` (finish-start)

### 16) Bitrix24 Task Result + Epic Auto-Close Rules (March 9, 2026)
- Added new mandatory workflow rules for Bitrix24 task operations:
  - when task is completed, write `Результат задачи` with done summary + commit link,
  - for epic/root tasks enable auto-close logic based on subtasks,
  - when epic is closed, append `Завершена` to title.
- Extended roadmap automation script:
  - `sync-task-results` mode in `scripts/bitrix24/roadmap_sync.py`
    - selects completed roadmap tasks from `docs/ROADMAP_EXECUTION_STATUS.json`
    - writes completion comment via `task.comment.add`
    - attempts binding as task result via `tasks.task.result.addFromComment`
  - `sync-epic-completion` mode
    - enables epic auto-close fields (`AUTOCOMPLETE_SUB_TASKS`, `SE_PARAMETER`)
    - closes epic when all its roadmap subtasks are completed
    - appends `Завершена` in epic title when closed.
- Updated operating docs and agent templates/skills:
  - `instructions/knowledge.md`
  - `instructions/agents/knowledge.md`
  - `instructions/agents/workflows.md`
  - `docs/CHAT_START_TEMPLATE.md`
  - `.cursor/skills/bitrix24-project-ops/SKILL.md`
  - `.claude/skills/bitrix24-project-ops/SKILL.md`
  - `scripts/README.md`
  - updates task statuses via `tasks.task.update`
- Updated operational script docs:
  - `scripts/README.md`
- Updated agent execution artifacts per architecture:
  - `.agent/plans/current-plan.md`
  - `.agent/context/session-summary.md`
  - `.agent/context/decision-log.jsonl`
  - `.agent/context/artifact-index.jsonl`

### 16) Bitrix24 Roadmap Publication (March 8, 2026)
- Received incoming webhook and project scope for operational tracking:
  - webhook: `https://rgflow.bitrix24.ru/rest/1/68atla5m26tf9rc6/`
  - `GROUP_ID=17`
- Executed roadmap publication using automation script:
  - `python3 scripts/bitrix24/roadmap_sync.py create --apply --project-id 17 --default-responsible-id 1`
- Result:
  - created all 24 roadmap tasks in Bitrix24 project
  - initialized statuses as `NEW`
  - created all dependency links (`finish-start`) from local roadmap graph
- Persisted roadmap mapping artifact for future status sync:
  - `.agent/context/bitrix-task-map.json`

### 17) Stage-1 Execution Control + RD-001 Completion (March 8, 2026)
- Extended roadmap automation script with metadata synchronization mode:
  - `sync-metadata` updates task titles/descriptions/tags from repository roadmap source.
- Introduced epic duplication in tags for all roadmap tasks (for board filtering).
- Updated all 24 Bitrix24 tasks in project `GROUP_ID=17` with enriched execution template:
  - what to do
  - skills to use
  - technical/UI testing approach
  - definition of done
  - workflow status mapping
- Added repository execution state file:
  - `docs/ROADMAP_EXECUTION_STATUS.json`
- Completed first execution task `RD-001` and moved through statuses:
  - `IN_PROGRESS (3)` -> `TESTING (4)` -> `DONE (5)`
- Added RD-001 artifact:
  - `docs/MVP_SCOPE_RELEASE_GATES.md`
- Paused further tasks by request; remaining roadmap tasks are kept in `NEW (1)`.

### 18) Workflow Guardrails: Bitrix24 Kanban Sync + VPS Deploy Verification (March 8, 2026)
- Implemented mandatory Bitrix24 project-ops automation updates in `scripts/bitrix24/roadmap_sync.py`:
  - new command `fetch-stages` (`task.stages.get`) to fetch actual kanban stages via webhook
  - `sync-status` can now move cards across kanban (`task.stages.movetask`) with permission check (`task.stages.canmovetask`)
  - webhook URL is now read from CLI arg or env (`B24_WEBHOOK_URL` in `.env` / `.env.webhooks`)
  - title convention enforced: human-readable title first, then `[RD-xxx][EPIC-xxx]`
  - task descriptions generated in Russian
- Live kanban stages synchronized from portal for project `GROUP_ID=17` and stored in:
  - `.agent/context/bitrix-kanban-stages.json`
- Re-synchronized all roadmap tasks metadata and statuses in Bitrix24 with new naming/description/tagging rules.
- Added secure env workflow for webhooks and project IDs:
  - updated `.env.example` with `B24_WEBHOOK_URL`, `B24_PROJECT_GROUP_ID`, VPS check vars
  - added `.env.webhooks.example`
  - updated `.gitignore` to ignore local webhook/vps env files
- Added mandatory post-push VPS verification script:
  - `scripts/vps/verify-sync.sh`
  - validates local/vps/origin commit sync + service status + health endpoint
- Created dedicated skill for Bitrix24 operational workflow:
  - `.cursor/skills/bitrix24-project-ops/SKILL.md`
  - `.claude/skills/bitrix24-project-ops/SKILL.md`
- Updated architecture docs/prompts/workflows/knowledge files with new global rules.

### 19) RD-002 Completed: CI Quality Baseline (March 8, 2026)
- Executed RD-002 through workflow statuses with Bitrix24+kanban synchronization:
  - `IN_PROGRESS (3)` -> `TESTING (4)` -> `DONE (5)`
- Added baseline quality tooling:
  - `scripts/quality-check.sh` (python syntax + roadmap JSON validation + frontend lint when pnpm is available)
  - `make quality-check` target in `makefile`
  - GitHub Actions workflow: `.github/workflows/quality-baseline.yml`
  - RD-002 deliverable doc: `docs/CI_QUALITY_BASELINE.md`
- Updated roadmap artifact:
  - refined RD-002 description in `docs/ROADMAP_TASKS.json`
- Updated operational docs:
  - `scripts/README.md` with new quality baseline command and behavior.
- Synced task metadata/statuses to Bitrix24 using updated automation workflow.

### 20) Preparatory Block + V1 Installation Milestone (March 8, 2026)
- Completed preparatory roadmap alignment and added missing tasks:
  - `RD-105` — V1 installer persistence + settings page
  - `RD-106` — create V2 after V1 approval
- Synchronized new tasks into Bitrix24 project and updated task-id map:
  - `RD-105` -> task `#235`
  - `RD-106` -> task `#237`
- Updated roadmap execution statuses and kanban transitions in Bitrix24:
  - marked `RD-003` as done (preparatory automation completed)
  - moved `RD-105` through `IN_PROGRESS -> TESTING -> DONE`
- Implemented V1 backend installer milestone:
  - enhanced install persistence in `features/installer/services.py`
  - added installation context API (`/api/pmo/installation-context`)
- Implemented V1 frontend settings milestone:
  - added `frontend/app/pages/settings.client.vue`
  - extended API store with `getInstallationContext`
  - install flow opens settings page after install finish
  - added index page shortcut to settings
- Added milestone documentation:
  - `docs/V1_INSTALLATION_DONE.md`

### 21) Installer Data Hardening After OAuth Audit (March 8, 2026)
- Verified required install/auth payload fields against Bitrix24 docs (OnAppInstall + OAuth simple flow).
- Improved account persistence on installation/auth refresh:
  - store `application_token` in `bitrix24account`
  - store `expires_in` and `current_scope`
- Fixed domain change save hook field typo:
  - `portal_url` -> `domain_url`
- Extended installation context output to include saved token/auth timing fields for V1 verification page.

### 22) Bitrix24 Epic/Subtask Board Restructure (March 9, 2026)
- Implemented new board model for Bitrix24 visualization:
  - epic = top-level base task
  - roadmap tasks = epic subtasks
  - nested subtasks driven by `parent` in roadmap source
- Extended `scripts/bitrix24/roadmap_sync.py`:
  - added `sync-epic-structure` command
  - auto-creates/updates epic root tasks
  - syncs parent links and gantt dependencies
  - adds safe handling for existing link/cycle conflicts
- Applied restructure to Bitrix24 project (`GROUP_ID=17`):
  - created epic roots: `EPIC-FND`, `EPIC-INS`, `EPIC-CORE`, `EPIC-OPS`, `EPIC-SEC`, `EPIC-V11`
  - re-parented roadmap tasks under epics
  - synced cross-epic gantt links between epic root tasks
- Updated mapping artifact to include epic IDs:
  - `.agent/context/bitrix-task-map.json` now has `epics` section.
- Updated docs/rules/skills to reflect new operational standard for Bitrix24 board structure.

### 23) Bitrix24 Subtask Numbering for Visual Hierarchy (March 9, 2026)
- Added hierarchical numbering in Bitrix24 task titles by epic tree level:
  - root task in epic: `Задача N.`
  - nested task: `Задача N.M.`
- Implemented numbering logic in roadmap sync automation:
  - `build_task_numbering`
  - title renderer `render_task_title_for_bitrix`
- Applied numbering to existing Bitrix24 board via `sync-epic-structure`.

### 24) Epic Numbering in Bitrix24 Board (March 9, 2026)
- Added explicit epic sequencing in epic task titles:
  - `Эпик 1 ...` through `Эпик 6 ...`
- Applied numbering via `sync-epic-structure` and verified titles in Bitrix24.

### 25) New VPS Recreated + Webhook Auto-Deploy Revalidated (March 14, 2026)
- Recreated infrastructure on a new server:
  - VPS: `5.42.119.99`
  - Domain: `pmo.russaldi.com`
- Bootstrap completed on VPS:
  - installed base packages (`docker.io`, `docker-compose-v2`, `nginx`, `certbot`, `ufw`, `git`, `make`)
  - created/validated `deploy` SSH user and key-based access
  - deployed app to `/opt/b24-ai-starter`
- Runtime and ops services configured:
  - `b24-ai-starter.service` (systemd)
  - `b24-webhook.service` (GitHub deploy webhook receiver)
  - helper commands: `b24-deploy`, `b24-status`, `b24-logs`
- TLS issued and enabled:
  - `https://pmo.russaldi.com` (Let's Encrypt + HTTP->HTTPS redirect)
- Deploy reliability hardening:
  - `b24-deploy` switched to deterministic flow (`fetch + reset --hard origin/master + clean -fd`)
  - python image source patched to `mirror.gcr.io/library/python:3.11-slim` to avoid Docker Hub `429` during rebuilds
- GitHub webhook endpoint validated end-to-end on new server:
  - route: `POST /deploy-webhook`
  - security: HMAC `X-Hub-Signature-256` + repo/ref filtering (`rustams/b24pmo`, `refs/heads/master`)
  - behavior: unsigned requests rejected; signed `ping` and signed `push` processed successfully
  - webhook-triggered deploy observed in server logs (`deploy success: OK: app https health => 200`)
- Repository/Bitrix24 task consistency check:
  - `docs/ROADMAP_TASKS.json` = 31 tasks
  - `docs/ROADMAP_EXECUTION_STATUS.json` = 31 status entries
  - `.agent/context/bitrix-task-map.json` = 31 mapped tasks, no missing keys
  - `sync-status --sync-kanban --apply` executed to align working group board with repository source-of-truth
- Final infra validation:
  - `./scripts/vps/verify-sync.sh` reports synchronized deploy (`HEALTH=200`, services active)
- Pending by design:
  - update VPS `.env` with final Bitrix24 `CLIENT_ID` and `CLIENT_SECRET` after new app registration for `https://pmo.russaldi.com`.

### 26) Idempotent Bitrix24 Roadmap Sync (No Duplicate Epics) (March 14, 2026)
- Fixed recurring duplicate epic creation during repeated `sync-epic-structure` runs.
- Introduced stable Bitrix identifiers in roadmap source-of-truth:
  - `docs/ROADMAP_TASKS.json` now contains `bitrix_ids.epics` and `bitrix_ids.tasks`.
- Hardened `scripts/bitrix24/roadmap_sync.py`:
  - `create` and `create-missing` now preload IDs from roadmap and discover existing project tasks by `[RD-xxx]` title keys before attempting create.
  - `sync-epic-structure` now preloads epic/task IDs from roadmap + map file + live Bitrix project scan.
  - stale mapping IDs are validated via `tasks.task.get`; when stale, script switches to discovered IDs or recreates only when truly missing.
  - epic root detection is constrained to titles with `[EPIC-xxx]` and without `[RD-xxx]`, reducing false positives.
- Verification:
  - `python3 scripts/bitrix24/roadmap_sync.py sync-epic-structure --project-id 17 --source docs/ROADMAP_TASKS.json --map-file .agent/context/bitrix-task-map.json --apply`
  - Result: existing epics updated in place (`EPIC-CORE/FND/INS/OPS/SEC/V11`), no new duplicate epic roots created.

### 27) Mandatory Context Skills + Epic-Aware Hierarchical Numbering (March 14, 2026)
- Project governance updated:
  - mandatory baseline skills for every task:
    - `context-engineering-collection`
    - `context-fundamentals`
    - `context-optimization`
  - reflected in project rules and agent guides (`.cursor/rules/*`, `instructions/agents/*`, `instructions/knowledge.md`, `docs/CHAT_START_TEMPLATE.md`, `CLAUDE.md`).
- Naming convention standardized and documented across workflows and Bitrix24 ops skills:
  - epic title: `Эпик N. ... [EPIC-XXX]`
  - first-level task in epic `N`: `Задача N.1 ...`
  - nested tasks: `Задача N.1.1 ...` and deeper.
- Automation updated:
  - `scripts/bitrix24/roadmap_sync.py` now generates epic-aware numbering prefixes in task titles.
- Applied to live Bitrix24 board:
  - `sync-epic-structure --apply` executed for `GROUP_ID=17`.
  - verified examples:
    - `RD-001`: `Задача 1.1...`
    - `RD-002`: `Задача 1.1.1...`
    - `RD-101`: `Задача 2.1...`
    - `RD-102`: `Задача 2.1.1...`
