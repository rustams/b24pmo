#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
if [[ -f .env.webhooks ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env.webhooks
  set +a
fi

VPS_DEPLOY_USER="${VPS_DEPLOY_USER:-deploy}"
VPS_DEPLOY_HOST="${VPS_DEPLOY_HOST:?Set VPS_DEPLOY_HOST in env}"
VPS_APP_PATH="${VPS_APP_PATH:-/opt/b24-ai-starter}"
VPS_HEALTH_URL="${VPS_HEALTH_URL:?Set VPS_HEALTH_URL in env}"

REMOTE="${VPS_DEPLOY_USER}@${VPS_DEPLOY_HOST}"
LOCAL_COMMIT="$(git rev-parse --short HEAD)"

REMOTE_LOCAL_COMMIT="$(ssh -o BatchMode=yes "$REMOTE" "cd '$VPS_APP_PATH' && git rev-parse --short HEAD")"
REMOTE_ORIGIN_COMMIT="$(ssh -o BatchMode=yes "$REMOTE" "cd '$VPS_APP_PATH' && git fetch origin --quiet >/dev/null 2>&1; git rev-parse --short origin/master")"
SERVICES="$(ssh -o BatchMode=yes "$REMOTE" "systemctl is-active b24-ai-starter b24-webhook")"
HEALTH_CODE="$(curl -s -o /dev/null -w '%{http_code}' "$VPS_HEALTH_URL")"

printf 'LOCAL_HEAD=%s\n' "$LOCAL_COMMIT"
printf 'VPS_HEAD=%s\n' "$REMOTE_LOCAL_COMMIT"
printf 'VPS_ORIGIN_MASTER=%s\n' "$REMOTE_ORIGIN_COMMIT"
printf 'SERVICES=\n%s\n' "$SERVICES"
printf 'HEALTH=%s\n' "$HEALTH_CODE"

if [[ "$LOCAL_COMMIT" != "$REMOTE_LOCAL_COMMIT" ]]; then
  echo "ERROR: VPS HEAD differs from local HEAD" >&2
  exit 2
fi
if [[ "$REMOTE_LOCAL_COMMIT" != "$REMOTE_ORIGIN_COMMIT" ]]; then
  echo "ERROR: VPS HEAD differs from origin/master" >&2
  exit 3
fi
while IFS= read -r service_state; do
  if [[ -z "$service_state" ]]; then
    continue
  fi
  if [[ "$service_state" != "active" ]]; then
    echo "ERROR: some required services are not active (state=$service_state)" >&2
    exit 4
  fi
done <<< "$SERVICES"
if [[ "$HEALTH_CODE" != "200" ]]; then
  echo "ERROR: health check is not 200" >&2
  exit 5
fi

echo "OK: VPS deploy is synchronized"
