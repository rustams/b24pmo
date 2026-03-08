# Deploy Workflow

## Recommended model
- Develop locally (Cursor/IDE on your PC)
- Commit + push to GitHub
- Deploy on VPS with one command: `b24-deploy master`

## VPS commands
- Status: `b24-status`
- Deploy: `b24-deploy master`
- Logs: `b24-logs` or `b24-logs 300`

## First setup on your PC
```bash
git clone <your-repo-url>
cd b24-ai-starter
git checkout -b dev
```

## Daily flow
```bash
# local
# edit -> commit -> push

git add .
git commit -m "feat: ..."
git push origin master

# vps
ssh root@85.239.54.74
b24-deploy master
```

## Release discipline (versions)
- Перед каждым релизом создавайте отдельную версию проекта:
```bash
make create-version VERSION=v2
```
- После выкладки фиксируйте номер версии в задаче/трекере (например, `v2`, `v3`).
- Если версия больше не нужна, удаляйте её через:
```bash
make delete-version VERSION=v2
```

## Important
- VPS repo currently uses runtime commits for mirror registry compatibility.
- Branch on VPS is `master`.
- If you switch to your own repo, update remote:
```bash
cd /opt/b24-ai-starter
git remote set-url origin <your-repo-url>
```
