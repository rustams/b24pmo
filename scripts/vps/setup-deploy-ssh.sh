#!/usr/bin/env bash
# Один раз выполнить НА VPS под root (скопировать и вставить в консоль root).
# Добавляет публичный ключ с Mac в authorized_keys root и deploy.
# Публичный ключ (id_ed25519) с машины разработки:
PUBKEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICypvpw/jAwvdPkDbQcgmh3SzB9VF91Aecq+A4WCD6/A salpagaroff@gmail.com'

set -e
mkdir -p /root/.ssh
grep -qF "$PUBKEY" /root/.ssh/authorized_keys 2>/dev/null || echo "$PUBKEY" >> /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys

mkdir -p /home/deploy/.ssh
grep -qF "$PUBKEY" /home/deploy/.ssh/authorized_keys 2>/dev/null || echo "$PUBKEY" >> /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

echo "OK: key added for root and deploy"
