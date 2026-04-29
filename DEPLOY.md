# Deployment Guide

## Local Windows

```text
start.bat
```

## Local Linux / macOS

```bash
chmod +x start.sh
./start.sh
```

## Docker

```bash
cp .env.example .env
docker compose up -d --build
```

Visit:

```text
http://127.0.0.1:8000
```

## Linux systemd

Example target directory:

```bash
sudo mkdir -p /opt/llm-orchestrator-dashboard
sudo cp -r . /opt/llm-orchestrator-dashboard
cd /opt/llm-orchestrator-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
sudo cp deploy/systemd/llm-orchestrator.service /etc/systemd/system/llm-orchestrator.service
sudo systemctl daemon-reload
sudo systemctl enable llm-orchestrator
sudo systemctl start llm-orchestrator
sudo systemctl status llm-orchestrator
```

## Nginx reverse proxy

```bash
sudo cp deploy/nginx/llm-orchestrator.conf /etc/nginx/sites-available/llm-orchestrator.conf
sudo ln -s /etc/nginx/sites-available/llm-orchestrator.conf /etc/nginx/sites-enabled/llm-orchestrator.conf
sudo nginx -t
sudo systemctl reload nginx
```

Edit `server_name your-domain.com;` before production use.

## Firewall

Ubuntu/Debian:

```bash
sudo ufw allow 8000/tcp
sudo ufw allow 80/tcp
```

Cloud providers also require opening TCP ports in Security Group / Firewall settings.
