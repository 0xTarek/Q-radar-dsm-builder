# Installation Guide
 
## Prerequisites

- Linux server (RHEL/CentOS 7+ or Ubuntu 18+)
- Python 2.7 or Python 3.x
- Network access to QRadar Console (port 443)
- A QRadar SEC token with Admin permissions

## Step-by-Step Installation

### Step 1 — Clone or download

```bash
git clone https://github.com/0xTarek/Q-radar-dsm-builder.git
cd Q-radar-dsm-builder
```

### Step 2 — Create deployment directory

```bash
sudo mkdir -p /opt/dsm-builder
sudo cp DSM_Builder.html /opt/dsm-builder/index.html
sudo cp dsm_server.py /opt/dsm-builder/dsm_server.py
```

### Step 3 — Test manually first

```bash
cd /opt/dsm-builder
python dsm_server.py
# or
python3 dsm_server.py
```

Open browser: `http://<server-ip>:8080/index.html`

Press `Ctrl+C` to stop when done testing.

### Step 4 — Check Python version

```bash
python --version   # Python 2.7
python3 --version  # Python 3.x
```

**If Python 2.7** → skip to Step 5 directly.

**If Python 3 only (Ubuntu/Debian)** → run these fixes first:

```bash
# Fix service file
sed -i 's|/usr/bin/python |/usr/bin/python3 |g' /etc/systemd/system/dsm-builder.service

# Fix Python 3 imports
sed -i 's|import urllib2|import urllib.request as urllib2|g' /opt/dsm-builder/dsm_server.py
sed -i 's|import BaseHTTPServer|import http.server as BaseHTTPServer|g' /opt/dsm-builder/dsm_server.py
sed -i 's|import SimpleHTTPServer|import http.server as SimpleHTTPServer|g' /opt/dsm-builder/dsm_server.py
```

### Step 5 — Install as systemd service

```bash
sudo cp dsm-builder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dsm-builder
sudo systemctl start dsm-builder
```

### Step 6 — Open firewall port (if needed)

```bash
# RHEL/CentOS
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# Ubuntu
sudo ufw allow 8080/tcp
```

### Step 7 — Verify

```bash
sudo systemctl status dsm-builder
curl http://localhost:8080/index.html | head -3
```

## Updating

```bash
cd Q-radar-dsm-builder
git pull
sudo cp DSM_Builder.html /opt/dsm-builder/index.html
sudo cp dsm_server.py /opt/dsm-builder/dsm_server.py
sudo systemctl restart dsm-builder
```

## Troubleshooting

**Python not found (status=203/EXEC):**
```bash
# Check which python you have
which python || which python3

# If Python 3 only — run the fixes in Step 4 above
# Then restart:
sudo systemctl reset-failed dsm-builder
sudo systemctl start dsm-builder
```

**Service fails to start:**
```bash
sudo journalctl -u dsm-builder -n 50
```

**Port 8080 already in use:**
```bash
sudo lsof -i :8080
# Edit dsm_server.py → change PORT = 8080 to another port
```

**QRadar API returns 401:**
- Check your SEC token is valid
- Verify token has Admin or appropriate permissions
- Token may have expired — regenerate in QRadar

**QRadar API returns 422:**
- AQL syntax issue — check QRadar version compatibility
- Try reducing the time window

**Logs return as Base64:**
- Normal — the tool automatically decodes Base64 PAYLOAD field
- If still garbled, open browser console (F12) for details
