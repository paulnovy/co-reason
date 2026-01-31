# Runbook — Product Optimizer

## URLs
- Front: http://<host>:5173
- API: http://<host>:8000/docs

## systemd user services
Recommended approach: run backend + frontend as `systemd --user` services.

### Install
```bash
mkdir -p ~/.config/systemd/user
cp scripts/systemd/product-optimizer-*.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now product-optimizer-api product-optimizer-front
```

### Restart
```bash
systemctl --user restart product-optimizer-api
systemctl --user restart product-optimizer-front
```

### Status
```bash
systemctl --user status product-optimizer-api product-optimizer-front
```

### Logs
```bash
journalctl --user -u product-optimizer-api -n 200 -f
journalctl --user -u product-optimizer-front -n 200 -f
```

## DB (PostgreSQL)
`docker-compose.yml` provides a dev Postgres instance.

```bash
sudo docker compose up -d db
```

## Troubleshooting
### Front tries port 5174
Port 5173 is already in use. Stop the old process, then restart the systemd service.

### API down
Restart the api unit:
```bash
systemctl --user restart product-optimizer-api
```
